import json
import requests
from typing import List, Dict, Any

class CarLLMSystem:
    def __init__(self, lm_studio_url: str = "http://localhost:1234"):
        """
        Inicializa o sistema LLM para consultas de carros
        
        Args:
            lm_studio_url: URL do servidor LM Studio (padrão: http://localhost:1234)
        """
        self.lm_studio_url = lm_studio_url
        self.cars_data = []
        
    def load_cars_data(self, json_file_path: str = "carros.json"):
        """
        Carrega os dados dos carros do arquivo JSON
        
        Args:
            json_file_path: Caminho para o arquivo JSON com os dados dos carros
        """
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                self.cars_data = json.load(file)
            print(f"✅ Carregados {len(self.cars_data)} carros do arquivo {json_file_path}")
        except FileNotFoundError:
            print(f"❌ Arquivo {json_file_path} não encontrado!")
            self.cars_data = []
        except json.JSONDecodeError as e:
            print(f"❌ Erro ao decodificar JSON: {e}")
            self.cars_data = []
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            self.cars_data = []
        
    def format_cars_for_prompt(self) -> str:
        """Formata os dados dos carros para o prompt do LLM"""
        formatted_cars = []
        
        for i, car in enumerate(self.cars_data, 1):
            car_info = f"""
Carro {i}:
- Marca: {car['detalhes']['marca']}
- Modelo: {car['detalhes']['modelo']}
- Título: {car['titulo']}
- Descrição: {car['descricao']}
- Ano: {car['anoModelo']}
- Preço: R$ {car['preco']}
- Quilometragem: {car['detalhes']['km']}
- Carroceria: {car['detalhes']['carroceria']}
- Motor: {car['detalhes']['motor']}
- Cor: {car['detalhes']['cor']}
- Câmbio: {car['detalhes']['câmbio']}
- Opcionais: {', '.join(car['detalhes']['opcionais'])}
"""
            formatted_cars.append(car_info)
            
        return '\n'.join(formatted_cars)
    
    def create_system_prompt(self) -> str:
        """Cria o prompt do sistema com os dados dos carros"""
        cars_info = self.format_cars_for_prompt()
        
        system_prompt = f"""
Você é um assistente especializado em veículos que tem acesso aos seguintes carros disponíveis:

{cars_info}

Instruções:
- Responda perguntas sobre estes carros de forma clara e objetiva
- Se perguntarem sobre carros específicos, use apenas as informações fornecidas
- Para comparações, apresente os dados de forma organizada
- Se não tiver a informação específica, diga que não possui essa informação
- Seja útil e amigável nas respostas
- Forneça preços sempre em reais (R$)
"""
        return system_prompt
    
    def query_llm(self, user_question: str) -> str:
        """
        Envia pergunta para o LLM via LM Studio
        
        Args:
            user_question: Pergunta do usuário sobre os carros
            
        Returns:
            Resposta do LLM
        """
        system_prompt = self.create_system_prompt()
        
        # Payload para a API do LM Studio
        payload = {
            "model": "mistral-7b-instruct-v0.1",  # Ajuste conforme o modelo carregado
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": user_question
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(
                f"{self.lm_studio_url}/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"Erro na requisição: {response.status_code} - {response.text}"
                
        except requests.exceptions.RequestException as e:
            return f"Erro de conexão: {str(e)}"
    
    def interactive_chat(self):
        """Modo de chat interativo"""
        print("=== Sistema de Consulta de Carros ===")
        print("Digite suas perguntas sobre os carros disponíveis.")
        print("Digite 'sair' para encerrar.\n")
        
        while True:
            user_input = input("Você: ").strip()
            
            if user_input.lower() in ['sair', 'exit', 'quit']:
                print("Encerrando o sistema. Até logo!")
                break
                
            if not user_input:
                continue
                
            print("Assistente: Processando...")
            response = self.query_llm(user_input)
            print(f"Assistente: {response}\n")

# Exemplo de uso do sistema
def main():
    # Inicializa o sistema
    car_system = CarLLMSystem()
    
    # Carrega os dados do arquivo carros.json
    car_system.load_cars_data("carros.json")
    
    # Verifica se os dados foram carregados
    if not car_system.cars_data:
        print("Nenhum dado de carro carregado. Verifique o arquivo carros.json")
        return
    
    # Exemplos de consultas programáticas
    print("=== Exemplos de Consultas ===")
    
    exemplos_perguntas = [
        "Quais carros estão disponíveis?",
        "Qual é o carro mais barato?",
        "Mostre-me carros com ar condicionado",
        "Qual carro tem menor quilometragem?",
        "Compare os preços dos carros Ford e Volkswagen"
    ]
    
    for pergunta in exemplos_perguntas:
        print(f"\n🤔 Pergunta: {pergunta}")
        resposta = car_system.query_llm(pergunta)
        print(f"🤖 Resposta: {resposta}")
        print("-" * 80)
    
    # Inicia o chat interativo
    print("\n" + "="*50)
    car_system.interactive_chat()

if __name__ == "__main__":
    main()