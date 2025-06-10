from flask import Flask, render_template, request, jsonify
import json
import re
import requests
from typing import List, Dict, Any, Optional

app = Flask(__name__)

class CarSystem:
    def __init__(self):
        """Sistema de consulta de carros para Flask"""
        self.cars_data = []
        self.load_cars_data()
        
    def load_cars_data(self, json_file_path: str = "carros.json"):
        """Carrega os dados dos carros do arquivo JSON"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                self.cars_data = json.load(file)
            print(f"✅ Carregados {len(self.cars_data)} carros")
            return True
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            self.cars_data = self.get_sample_data()
            return False
    
    def get_sample_data(self):
        """Dados de exemplo caso o arquivo não exista"""
        return [
            # (Dados de exemplo mantidos como no código original)
            # ... [mantém o mesmo conteúdo do método get_sample_data original]
        ]
    
    def format_price(self, price_str: str) -> float:
        """Converte string de preço para float"""
        try:
            clean_price = price_str.replace('.', '').replace(',', '.')
            return float(clean_price)
        except:
            return 0.0
    
    def format_km(self, km_str: str) -> float:
        """Converte string de quilometragem para float"""
        try:
            numbers = re.findall(r'\d+', km_str.replace('.', ''))
            if numbers:
                return float(numbers[0])
            return 0.0
        except:
            return 0.0
    
    def get_all_cars(self):
        """Retorna todos os carros"""
        return self.cars_data
    
    def find_cheapest_car(self):
        """Encontra o carro mais barato"""
        if not self.cars_data:
            return None
        return min(self.cars_data, key=lambda x: self.format_price(x['preco']))
    
    def find_most_expensive_car(self):
        """Encontra o carro mais caro"""
        if not self.cars_data:
            return None
        return max(self.cars_data, key=lambda x: self.format_price(x['preco']))
    
    def find_lowest_mileage(self):
        """Encontra o carro com menor quilometragem"""
        if not self.cars_data:
            return None
        return min(self.cars_data, key=lambda x: self.format_km(x['detalhes']['km']))
    
    def find_cars_by_brand(self, brand: str):
        """Encontra carros por marca"""
        return [car for car in self.cars_data 
                if brand.upper() in car['detalhes']['marca'].upper()]
    
    def find_cars_with_feature(self, feature: str):
        """Encontra carros com um opcional específico"""
        cars_with_feature = []
        feature_lower = feature.lower()
        
        for car in self.cars_data:
            for opcional in car['detalhes']['opcionais']:
                if feature_lower in opcional.lower():
                    cars_with_feature.append(car)
                    break
        return cars_with_feature
    
    def search_cars(self, query: str):
        """Busca carros baseado em query"""
        query_lower = query.lower()
        results = []
        for brand in ['ford', 'volkswagen', 'fiat']:
            if brand in query_lower:
                results.extend(self.find_cars_by_brand(brand))
        if 'ar condicionado' in query_lower:
            results.extend(self.find_cars_with_feature('ar condicionado'))
        elif 'direção' in query_lower:
            results.extend(self.find_cars_with_feature('direção'))
        elif 'air bag' in query_lower:
            results.extend(self.find_cars_with_feature('air bag'))
        seen = set()
        unique_results = []
        for car in results:
            car_id = car['titulo']
            if car_id not in seen:
                seen.add(car_id)
                unique_results.append(car)
        return unique_results if unique_results else self.cars_data

class CarLLMSystem:
    def __init__(self, lm_studio_url: str = "http://localhost:1234"):
        self.lm_studio_url = lm_studio_url
        self.cars_data = []
        self.load_cars_data()
        
    def load_cars_data(self, json_file_path: str = "carros.json"):
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
    
    def query_llm(self, user_question: str, history: List[Dict[str, str]]) -> str:
        system_prompt = self.create_system_prompt()
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_question})
        
        payload = {
            "model": "mistral-7b-instruct-v0.1",
            "messages": messages,
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

# Inicializa os sistemas
car_system = CarSystem()
car_llm_system = CarLLMSystem()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/cars')
def api_cars():
    return jsonify(car_system.get_all_cars())

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    cars = car_system.search_cars(query)
    return jsonify(cars)

@app.route('/api/filter/<filter_type>')
def api_filter(filter_type):
    if filter_type == 'cheapest':
        car = car_system.find_cheapest_car()
        return jsonify([car] if car else [])
    elif filter_type == 'expensive':
        car = car_system.find_most_expensive_car()
        return jsonify([car] if car else [])
    elif filter_type == 'lowest_km':
        car = car_system.find_lowest_mileage()
        return jsonify([car] if car else [])
    else:
        return jsonify([])

@app.route('/api/brand/<brand>')
def api_brand(brand):
    cars = car_system.find_cars_by_brand(brand)
    return jsonify(cars)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    try:
        data = request.get_json()
        message = data.get('message', '')
        history = data.get('history', [])
        if not message:
            return jsonify({"success": False, "response": "Nenhuma mensagem fornecida"})
        
        response = car_llm_system.query_llm(message, history)
        return jsonify({"success": True, "response": response})
    except Exception as e:
        print(f"Erro no endpoint /api/chat: {e}")
        return jsonify({"success": False, "response": "Erro ao processar a solicitação"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)