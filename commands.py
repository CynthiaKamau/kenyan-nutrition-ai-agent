"""Command reference for training and running the Kenyan Nutrition Agent."""

COMMANDS = {
	"activate_venv": "source .venv/bin/activate",
	"train_local_model": (
		"/home/cynthia/Work/kenyan-nutrition-ai-agent/.venv/bin/python "
		"models/fine_tuned/train_local_evaluator.py "
		"--dataset kenya_food_dataset.json "
		"--output models/fine_tuned/local_evaluator.joblib "
		"--max-meals-per-group 200"
	),
	"train_local_model_tuned": (
		"/home/cynthia/Work/kenyan-nutrition-ai-agent/.venv/bin/python "
		"models/fine_tuned/train_local_evaluator.py "
		"--dataset kenya_food_dataset.json "
		"--output models/fine_tuned/local_evaluator.joblib "
		"--max-meals-per-group 200 "
		"--enable-search --cv-folds 5 --search-iterations 20"
	),
	"local_model_accuracy_report": (
		"/home/cynthia/Work/kenyan-nutrition-ai-agent/.venv/bin/python "
		"evaluation/local_model_report.py "
		"--dataset kenya_food_dataset.json "
		"--model-path models/fine_tuned/local_evaluator.joblib "
		"--max-meals-per-group 200 --top-k 10 --split-strategy random"
	),
	"local_model_accuracy_report_grouped": (
		"/home/cynthia/Work/kenyan-nutrition-ai-agent/.venv/bin/python "
		"evaluation/local_model_report.py "
		"--dataset kenya_food_dataset.json "
		"--model-path models/fine_tuned/local_evaluator.joblib "
		"--max-meals-per-group 200 --top-k 10 --split-strategy group --importance-top-k 8"
	),
	"generate_training_samples": (
		"/home/cynthia/Work/kenyan-nutrition-ai-agent/.venv/bin/python "
		"pipelines/dataset_builder.py"
	),
	"run_metrics": (
		"/home/cynthia/Work/kenyan-nutrition-ai-agent/.venv/bin/python "
		"evaluation/metrics.py"
	),
	"set_local_model_env": "export CUSTOM_EVALUATOR_MODEL=local:models/fine_tuned/local_evaluator.joblib",
	"run_agent": "python3 agent.py",
}


if __name__ == "__main__":
	for name, command in COMMANDS.items():
		print(f"{name}:\n  {command}\n")
