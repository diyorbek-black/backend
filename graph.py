from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from app.llm.providers import call_llm
from app.security import decrypt_api_key


class AgentState(TypedDict):
    user_query: str
    proposals: List[dict]
    critique_feedback: Optional[str]
    final_output: Optional[str]


ROLE_ORDER = ["Architect", "Creative", "Guardian", "Critic", "Executor"]


async def _ask_agent(agent: dict, prompt: str) -> str:
    """Agentga (istalgan protocol/provayder) so'rov yuboradi, kalitni deshifrlab ishlatadi."""
    decrypted_key = decrypt_api_key(agent["api_key"])
    return await call_llm(
        protocol=agent["protocol"],
        base_url=agent["base_url"],
        api_key=decrypted_key,
        model=agent["model"],
        system_prompt=agent["system_prompt"],
        user_message=prompt,
    )


def _make_proposal_node(agent: dict):
    async def node(state: AgentState):
        proposals_text = "\n".join(
            f"- {p['agent_name']} ({p['role']}): {p['text']}" for p in state["proposals"]
        ) or "(hali takliflar yo'q)"
        prompt = (
            f"Foydalanuvchi so'rovi: {state['user_query']}\n\n"
            f"Hozirgacha jamlangan takliflar:\n{proposals_text}\n\n"
            f"O'z rolingga ({agent['role']}) mos taklifingni ber."
        )
        text = await _ask_agent(agent, prompt)
        new_proposal = {"agent_name": agent["name"], "role": agent["role"], "text": text}
        return {"proposals": state["proposals"] + [new_proposal]}

    return node


def _make_critic_node(agent: dict):
    async def node(state: AgentState):
        proposals_text = "\n".join(
            f"- {p['agent_name']} ({p['role']}): {p['text']}" for p in state["proposals"]
        )
        prompt = (
            f"Foydalanuvchi so'rovi: {state['user_query']}\n\n"
            f"Takliflar:\n{proposals_text}\n\n"
            f"Ushbu takliflarni tanqidiy tahlil qil: zaif tomonlari, xatolari, "
            f"xavfsizlik muammolarini ko'rsat."
        )
        feedback = await _ask_agent(agent, prompt)
        return {"critique_feedback": feedback}

    return node


def _make_executor_node(agent: dict):
    async def node(state: AgentState):
        proposals_text = "\n".join(
            f"- {p['agent_name']} ({p['role']}): {p['text']}" for p in state["proposals"]
        )
        prompt = (
            f"Foydalanuvchi so'rovi: {state['user_query']}\n\n"
            f"Takliflar:\n{proposals_text}\n\n"
            f"Tanqidchi fikri: {state.get('critique_feedback') or 'Yo\u2018q'}\n\n"
            f"Barcha fikrlarni jamlab, foydalanuvchiga yakuniy, aniq va amaliy javob ber."
        )
        final = await _ask_agent(agent, prompt)
        return {"final_output": final}

    return node


def build_graph(agents: List[dict]):
    """
    agents — foydalanuvchining faol agentlari ro'yxati (har biri dict:
    name, role, provider_label, protocol, base_url, api_key(shifrlangan), model, system_prompt).
    Rollarga qarab dinamik LangGraph quriladi: Architect -> Creative -> Guardian -> Critic -> Executor
    (mavjud bo'lmagan rollar avtomatik o'tkazib yuboriladi).
    """
    by_role: dict[str, list[dict]] = {}
    for a in agents:
        by_role.setdefault(a["role"], []).append(a)

    present_roles = [r for r in ROLE_ORDER if r in by_role]
    if not present_roles:
        raise ValueError("Hech qanday faol agent topilmadi")

    workflow = StateGraph(AgentState)
    node_names: List[str] = []

    for role in present_roles:
        for idx, agent in enumerate(by_role[role]):
            node_name = f"{role.lower()}_{idx}"
            if role == "Critic":
                workflow.add_node(node_name, _make_critic_node(agent))
            elif role == "Executor":
                workflow.add_node(node_name, _make_executor_node(agent))
            else:
                workflow.add_node(node_name, _make_proposal_node(agent))
            node_names.append(node_name)

    # Agar alohida Executor agenti bo'lmasa, oxirgi tugundan keyin
    # avtomatik "yakunlovchi" tugun qo'shiladi (oxirgi rol agentidan foydalanib).
    if not any(n.startswith("executor_") for n in node_names):
        last_agent = by_role[present_roles[-1]][-1]
        workflow.add_node("executor_fallback", _make_executor_node(last_agent))
        node_names.append("executor_fallback")

    workflow.set_entry_point(node_names[0])
    for i in range(len(node_names) - 1):
        workflow.add_edge(node_names[i], node_names[i + 1])
    workflow.add_edge(node_names[-1], END)

    return workflow.compile()


async def run_orchestration(agents: List[dict], user_query: str) -> AgentState:
    graph = build_graph(agents)
    initial_state: AgentState = {
        "user_query": user_query,
        "proposals": [],
        "critique_feedback": None,
        "final_output": None,
    }
    result = await graph.ainvoke(initial_state)
    return result
