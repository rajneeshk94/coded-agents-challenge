from flask import Flask, request, jsonify
from graph import appraisal_graph

app = Flask(__name__)

@app.route("/check", methods=["POST"])
def check():
    try:

        data = request.json
        candidate_input = data["candidate"]

        inputs = {
            "candidate_input": candidate_input
        }

        final_state = appraisal_graph.invoke(inputs)

        candidate = final_state.get("candidate")
        result = final_state.get("result")
        skill_gap = final_state.get("skill_gap")

        return jsonify({
            "candidate_name": candidate.name if candidate else None,
            "eligible": result.is_eligible if result else None,
            "reasons": result.reasons if result else [],
            "suggested_role": result.suggested_role if result else None,
            "skill_gap": skill_gap
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)