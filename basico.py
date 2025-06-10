from venv.car_llm_system import CarLLMSystem

# Inicializa o sistema
car_system = CarLLMSystem()

# Carrega os dados
car_system.load_cars_data("carros.json")

# Faz uma pergunta
resposta = car_system.query_llm("Qual o carro mais barato?")
print(resposta)