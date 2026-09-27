'''CLI for the energy assistant.'''

import argparse
import json
from decimal import Decimal
from pathlib import Path

from langchain_core.messages import ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from .data import EnergyData
from .graph import build_graph
from .tools import make_tools


ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description="Energy Assistant")
    parser.add_argument("--csv", type=Path, default=ROOT / "simulated_energy_data_aug.csv")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs")
    parser.add_argument("--query", help="Handle one request and exit")
    args = parser.parse_args()

    data = EnergyData(args.csv)
    graph = build_graph(
        ChatGoogleGenerativeAI(model="gemini-3.8-flash"),
        make_tools(data, args.output_dir),
        data,
    )

    def respond(query):
        result = graph.invoke({"messages": [("user", query)]})
        message = result["messages"][-1]
        if isinstance(message, ToolMessage):
            values = json.loads(message.content)
            if "error" in values:
                print(values["error"])
            elif values["action"] == "total":
                print(f'{values["kwh"]} kWh from {values["start"]} through {values["end"]}.')
            else:
                print(
                    f'{values["kwh"]} kWh at SGD {values["tariff"]}/kWh = '
                    f'SGD {values["amount"]}. Invoice: {values["file"]}'
                )
        else:
            print(message.content)

    if args.query:
        respond(args.query)
        return

    print(f"Energy Assistant ({data.first_date} to {data.last_date}). Type 'exit' to quit.")
    while True:
        try:
            query = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if query.lower() in {"exit", "quit"}:
            break
        if query:
            respond(query)
    print("Goodbye.")
