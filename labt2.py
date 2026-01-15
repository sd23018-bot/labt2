import json
import operator
import streamlit as st


OPS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
}


RULES = [
    {
        "name": "Windows open → turn AC off",
        "priority": 100,
        "conditions": [
            ["windows_open", "==", True]
        ],
        "action": {
            "ac_mode": "OFF",
            "fan_speed": "LOW",
            "setpoint": None,
            "reason": "Windows are open"
        }
    },
    {
        "name": "No one home → eco mode",
        "priority": 90,
        "conditions": [
            ["occupancy", "==", "EMPTY"],
            ["temperature", ">=", 24]
        ],
        "action": {
            "ac_mode": "ECO",
            "fan_speed": "LOW",
            "setpoint": 27,
            "reason": "Home empty; save energy"
        }
    },
    {
        "name": "Hot & humid (occupied) → cool strong",
        "priority": 80,
        "conditions": [
            ["occupancy", "==", "OCCUPIED"],
            ["temperature", ">=", 30],
            ["humidity", ">=", 70]
        ],
        "action": {
            "ac_mode": "COOL",
            "fan_speed": "HIGH",
            "setpoint": 23,
            "reason": "Hot and humid"
        }
    },
    {
        "name": "Hot (occupied) → cool",
        "priority": 70,
        "conditions": [
            ["occupancy", "==", "OCCUPIED"],
            ["temperature", ">=", 28]
        ],
        "action": {
            "ac_mode": "COOL",
            "fan_speed": "MEDIUM",
            "setpoint": 24,
            "reason": "Temperature high"
        }
    },
    {
        "name": "Slightly warm (occupied) → gentle cool",
        "priority": 60,
        "conditions": [
            ["occupancy", "==", "OCCUPIED"],
            ["temperature", ">=", 26],
            ["temperature", "<", 28]
        ],
        "action": {
            "ac_mode": "COOL",
            "fan_speed": "LOW",
            "setpoint": 25,
            "reason": "Slightly warm"
        }
    },
    {
        "name": "Night (occupied) → sleep mode",
        "priority": 75,
        "conditions": [
            ["occupancy", "==", "OCCUPIED"],
            ["time_of_day", "==", "NIGHT"],
            ["temperature", ">=", 26]
        ],
        "action": {
            "ac_mode": "SLEEP",
            "fan_speed": "LOW",
            "setpoint": 26,
            "reason": "Night comfort"
        }
    },
    {
        "name": "Too cold → turn off",
        "priority": 85,
        "conditions": [
            ["temperature", "<=", 22]
        ],
        "action": {
            "ac_mode": "OFF",
            "fan_speed": "LOW",
            "setpoint": None,
            "reason": "Already cold"
        }
    }
]


def evaluate_condition(facts, cond):
    """Evaluate a single condition: [field, operator, value]."""
    field, op, value = cond
    if field not in facts or op not in OPS:
        return False
    try:
        return OPS[op](facts[field], value)
    except Exception:
        return False


def rule_matches(facts, rule):
    """Check if all conditions in a rule are satisfied (AND logic)."""
    return all(evaluate_condition(facts, c) for c in rule.get("conditions", []))


def run_rules(facts, rules):
    fired = [r for r in rules if rule_matches(facts, r)]
    if not fired:
        return {"ac_mode": "OFF", "fan_speed": "LOW", "setpoint": None, "reason": "No rules matched"}
    fired_sorted = sorted(fired, key=lambda r: r.get("priority", 0), reverse=True)
    best = fired_sorted[0]["action"]
    return best


st.set_page_config(page_title="Smart Home AC Controller", layout="wide")
st.title("Smart Home Air Conditioner Controller")
st.caption("Enter your home conditions and evaluate the optimal AC settings.")


with st.sidebar:
    st.header("Home Conditions")
    temperature = st.number_input("Temperature (°C)", min_value=10, max_value=50, value=22)
    humidity = st.number_input("Humidity (%)", min_value=0, max_value=100, value=46)
    occupancy = st.selectbox("Occupancy", ["OCCUPIED", "EMPTY"], index=0)
    time_of_day = st.selectbox("Time of Day", ["MORNING", "AFTERNOON", "EVENING", "NIGHT"], index=3)
    windows_open = st.checkbox("Windows Open", value=False)


facts = {
    "temperature": float(temperature),
    "humidity": int(humidity),
    "occupancy": occupancy,
    "time_of_day": time_of_day,
    "windows_open": windows_open
}


st.subheader("Current Home Facts")
st.json(facts)


if st.button("Evaluate AC Settings"):
    result = run_rules(facts, RULES)
    
    st.subheader("AC Settings Recommendation")
    st.write(f"**AC Mode:** {result['ac_mode']}")
    st.write(f"**Fan Speed:** {result['fan_speed']}")
    st.write(f"**Setpoint Temperature:** {result['setpoint']}")
    st.write(f"**Reason:** {result['reason']}")

