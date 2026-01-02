from django.core.management.base import BaseCommand
from django.utils.text import slugify
from problems.models import Problem, TestCase
from problems.ai.problem_generator import generate_problem
import random
import uuid

TOPICS = ["arrays", "strings", "graphs", "math", "dp", "recursion", "searching", "sorting"]
DIFFICULTIES = ["easy", "medium", "hard"]

TOPIC_DEFAULTS = {
    "arrays": [
        {"args": [[1, 2, 3, 4, 5]], "output": "15"},
        {"args": [[]], "output": "0"},
        {"args": [[10, 20, 30]], "output": "60"}
    ],
    "strings": [
        {"args": ["hello"], "output": "olleh"},
        {"args": ["a"], "output": "a"},
        {"args": ["python"], "output": "nohtyp"}
    ],
    "math": [
        {"args": [5], "output": "120"},
        {"args": [0], "output": "1"},
        {"args": [3], "output": "6"}
    ],
    "sorting": [
        {"args": [[3, 1, 4, 1, 5]], "output": "[1, 1, 3, 4, 5]"},
        {"args": [[]], "output": "[]"},
        {"args": [[5, 4, 3, 2, 1]], "output": "[1, 2, 3, 4, 5]"}
    ],
    "searching": [
        {"args": [[1, 3, 5, 7], 5], "output": "2"},
        {"args": [[1, 3, 5, 7], 1], "output": "0"},
        {"args": [[1, 3, 5, 7], 8], "output": "-1"}
    ],
    "graphs": [
        {"args": [[[1, 2], [2, 3]]], "output": "3"},
        {"args": [[[0, 1]]], "output": "2"},
        {"args": [[[1, 2], [2, 3], [3, 1]]], "output": "3"}
    ],
    "dp": [
        {"args": [[1, 2, 3]], "output": "4"},
        {"args": [[2, 1]], "output": "2"},
        {"args": [[1]], "output": "1"}
    ],
    "recursion": [
        {"args": [5], "output": "120"},
        {"args": [0], "output": "1"},
        {"args": [3], "output": "6"}
    ]
}

def generate_acceptance(difficulty):
    if difficulty == "easy":
        return round(random.uniform(60, 90), 2)
    elif difficulty == "medium":
        return round(random.uniform(40, 70), 2)
    else:
        return round(random.uniform(20, 50), 2)

class Command(BaseCommand):
    help = "Generate coding problems using AI with exactly 3 test cases per problem."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=10)

    def handle(self, *args, **options):
        total = options["count"]
        self.stdout.write(self.style.WARNING(f"⚡ Generating {total} AI problems with 3 test cases each..."))

        for i in range(total):
            difficulty = random.choice(DIFFICULTIES)
            topic = random.choice(TOPICS)

            # AI GENERATES PROBLEM 
            try:
                data = generate_problem(difficulty, topic)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"AI Error: {e}"))
                continue

            # Extract function name 
            function_name = data.get("function_name", "solution")
            
            # Generate Slug
            raw_title = data.get("title", f"Untitled-{uuid.uuid4().hex[:6]}")
            slug = slugify(raw_title)
            if len(slug) > 200:
                slug = slug[:200]

            if Problem.objects.filter(slug=slug).exists():
                slug = f"{slug[:180]}-{uuid.uuid4().hex[:6]}"

            #  Ensure examples have explanations 
            examples = data.get("examples", [])
            for ex in examples:
                if "explanation" not in ex:
                    ex["explanation"] = ""

            # Create Problem 
            problem = Problem.objects.create(
                title=raw_title,
                slug=slug,
                difficulty=difficulty,
                category=topic,
                acceptance=generate_acceptance(difficulty),
                description=data.get("description", ""),
                examples=examples,
                starter_code=data.get("starter_code", {}),
                constraints=data.get("constraints", []),
                tags=data.get("tags", []),
            )

            self.stdout.write(self.style.SUCCESS(f"Problem Created: {problem.title}"))
            self.stdout.write(f"  Function: {function_name}")

            # Add Test Cases
            test_cases_data = data.get("test_cases", [])
            
            if not test_cases_data or len(test_cases_data) == 0:
                self.stdout.write(self.style.WARNING(f"⚠ Using {topic}-specific defaults"))
                test_cases_data = TOPIC_DEFAULTS.get(topic, TOPIC_DEFAULTS["arrays"])

            test_cases_data = test_cases_data[:3]

            for order, tc in enumerate(test_cases_data, start=1):
                args = tc.get("args", [])
                expected_output = str(tc.get("output", ""))                
                clean_input = ", ".join(str(arg) for arg in args)
                
                TestCase.objects.create(
                    problem=problem,
                    input=clean_input,
                    output=expected_output,
                    hidden=False,
                    order=order,
                )

            self.stdout.write(self.style.SUCCESS(f"Added {len(test_cases_data)} test cases"))

        self.stdout.write(self.style.SUCCESS("All AI problems generated successfully!"))