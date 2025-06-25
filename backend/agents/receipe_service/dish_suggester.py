# services/dish_suggester.py
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from agents.receipe_service.llm_config import get_llm

# Load LLM (you may configure this further as needed)
llm = get_llm(provider='github')

prompt = PromptTemplate(
    input_variables=["input"],
    template=(
        "You are a helpful cooking assistant.\n"
        "Given the following user input: {input}\n\n"
        "Your task is to suggest exactly one dish that can be prepared using the ingredients provided.\n\n"
        "Always return a JSON object containing:\n"
        "- 'dish_name': the name of the suggested dish\n"
        "- 'ingredients': a dictionary where each key is an ingredient and each value is its quantity and description\n\n"
        "Only include a third field, 'instructions', if the user's input explicitly asks for a recipe, cooking instructions, preparation steps, or uses similar keywords such as: 'how to make', 'steps', 'recipe', 'instructions', or 'how do I cook'.\n"
        "If instructions are not requested, do NOT include the 'instructions' field.\n\n"
        "If instructions are NOT requested:\n"
        "{{\n"
        '  "dish_name": "<Dish Name>",\n'
        '  "ingredients": {{\n'
        '    "<Ingredient 1>": "<Quantity and description>",\n'
        '    "<Ingredient 2>": "<Quantity and description>"\n'
        "  }}\n"
        "}}\n\n"
        "If instructions ARE requested:\n"
        "{{\n"
        '  "dish_name": "<Dish Name>",\n'
        '  "ingredients": {{\n'
        '    "<Ingredient 1>": "<Quantity and description>",\n'
        '    "<Ingredient 2>": "<Quantity and description>"\n'
        "  }},\n"
        '  "instructions": {{\n'
        '    "Step1": "<Step 1 description>",\n'
        '    "Step2": "<Step 2 description>"\n'
        "  }}\n"
        "}}"
    )
)

dish_suggestion_chain = LLMChain(llm=llm, prompt=prompt)

def suggest_dish(ingredients: str) -> str:
    response = dish_suggestion_chain.invoke({"input": ingredients})
    return response['text']
