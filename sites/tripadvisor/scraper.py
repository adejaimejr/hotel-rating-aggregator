"""
TripAdvisor Scraper - Estilo Original Que Funcionava
===================================================

Baseado no payload original capturado do navegador que estava funcionando.
Abordagem simples e direta sem complicações.
"""

import json
import time
import random
import secrets
import gzip
import zlib
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests


class TripAdvisorScraper:
    """Scraper TripAdvisor - Estilo original simples que funcionava"""
    
    def __init__(self):
        """Inicializa o scraper com configurações funcionais"""
        self.base_url = "https://www.tripadvisor.com.br/data/graphql/ids"
        self.timeout = 15
        
    def _get_real_headers(self) -> Dict[str, str]:
        """Headers reais capturados do navegador que funcionavam"""
        return {
            'accept': '*/*',
            'accept-language': 'pt-BR,pt;q=0.9',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'origin': 'https://www.tripadvisor.com.br',
            'pragma': 'no-cache',
            'referer': 'https://www.tripadvisor.com.br/',
            'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'same-origin',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
        }
    
    def _get_real_cookies(self) -> Dict[str, str]:
        """Cookies base realistas para sessão válida"""
        session_id = secrets.token_hex(16).upper()
        timestamp = int(time.time())
        
        return {
            'TASID': session_id,
            'TASession': f'V2ID.{session_id}*SQ.1*LS.Hotel_Review*HS.recommended*ES.popularity*DS.5*SAS.popularity*FPS.oldFirst*FA.1*DF.0*TRA.true',
            'TATrkConsent': 'eyJvdXQiOiJTT0NJQUxfTUVESUEiLCJpbiI6IkFEVixBTkEsRlVOQ1RJT05BTCJ9',
            'OptanonConsent': f'isGpcEnabled=0&datestamp={datetime.now().strftime("%a+%b+%d+%Y+%H%%3A%M%%3A%S")}',
            '_ga': f'GA1.1.{random.randint(100000000, 999999999)}.{timestamp}',
            '_gcl_au': f'1.1.{random.randint(100000000, 999999999)}.{timestamp}'
        }
    
    def _build_payload_for_hotel(self, hotel_id: int) -> List[Dict]:
        """Constrói payload baseado no original que funcionava"""
        session_id = secrets.token_hex(16).upper()
        page_uid = f"{secrets.token_hex(4)}-{secrets.token_hex(2)}-{secrets.token_hex(2)}-{secrets.token_hex(2)}-{secrets.token_hex(6)}"
        
        # Payload original adaptado para qualquer hotel
        return [
            {
                "variables": {"page": "Hotel_Review", "platform": "mobileweb"},
                "extensions": {"preRegisteredQueryId": "b4613962d98df032"}
            },
            {
                "variables": {"locationId": hotel_id},
                "extensions": {"preRegisteredQueryId": "5b064920a1417d48"}
            },
            {
                "variables": {
                    "deviceType": "MOBILE",
                    "trafficSource": "ba",
                    "locationId": hotel_id,
                    "geoId": 644400,  # Alagoas geo ID
                    "servletName": "Hotel_Review",
                    "hotelTravelInfo": None,
                    "language": "pt",
                    "isJp": False
                },
                "extensions": {"preRegisteredQueryId": "85513b806d5405da"}
            },
            {
                "variables": {
                    "locationId": hotel_id,
                    "trafficSource": "ba", 
                    "deviceType": "MOBILE",
                    "servletName": "Hotel_Review",
                    "hotelTravelInfo": None,
                    "withContactLinks": False
                },
                "extensions": {"preRegisteredQueryId": "d9072109f7378ce1"}
            },
            {
                "variables": {
                    "locationId": hotel_id,
                    "currencyCode": "BRL",
                    "sessionId": session_id,
                    "pageviewUid": page_uid,
                    "travelInfo": None,
                    "requestNumber": 0,
                    "filters": None,
                    "route": {
                        "page": "Hotel_Review",
                        "params": {"geoId": 644400, "detailId": hotel_id}
                    },
                    "application": "HOTEL_DETAIL",
                    "requestCaller": "Hotel_Review",
                    "loadReviewSnippets": True
                },
                "extensions": {"preRegisteredQueryId": "b6da76ae151e9c7c"}
            }
        ]
    
    def _extract_rating_data(self, response_data: List[Dict]) -> Optional[Dict]:
        """Extrai dados de rating da resposta - estilo original"""
        try:
            # Procura por reviewSummaryInfo nos resultados
            for result in response_data:
                if 'data' in result:
                    data = result['data']
                    
                    # Estratégia 1: reviewSummaryInfo direto
                    if 'reviewSummaryInfo' in data:
                        review_info = data['reviewSummaryInfo']
                        if isinstance(review_info, list) and len(review_info) > 0:
                            response_data_item = review_info[0].get('responseData', {})
                            if 'rating' in response_data_item and 'count' in response_data_item:
                                return {
                                    'rating': response_data_item['rating'],
                                    'review_count': response_data_item['count'],
                                    'source': 'reviewSummaryInfo'
                                }
                    
                    # Estratégia 2: location info
                    if 'location' in data:
                        location = data['location']
                        if 'rating' in location or 'numberOfReviews' in location:
                            return {
                                'rating': location.get('rating', 0),
                                'review_count': location.get('numberOfReviews', 0),
                                'source': 'location'
                            }
                    
                    # Estratégia 3: locations array
                    if 'locations' in data:
                        locations = data['locations']
                        if isinstance(locations, list) and len(locations) > 0:
                            location = locations[0]
                            if 'rating' in location or 'numberOfReviews' in location:
                                return {
                                    'rating': location.get('rating', 0),
                                    'review_count': location.get('numberOfReviews', 0),
                                    'source': 'locations'
                                }
            
            print("❌ Nenhuma estrutura de dados reconhecida encontrada")
            return None
            
        except Exception as e:
            print(f"❌ Erro ao extrair dados: {e}")
            return None
    
    def scrape_hotel(self, hotel_url: str, hotel_name: str) -> Optional[Dict[str, Any]]:
        """Scrapa dados de um hotel - estilo original simples"""
        print(f"\n🎯 Extraindo: {hotel_name}")
        
        # Extrai ID do hotel da URL
        hotel_id = self._extract_hotel_id(hotel_url)
        if not hotel_id:
            print(f"❌ ID não encontrado na URL: {hotel_url}")
            return None
        
        print(f"📋 Hotel ID: {hotel_id}")
        
        # Cria sessão nova
        session = requests.Session()
        session.headers.update(self._get_real_headers())
        session.cookies.update(self._get_real_cookies())
        
        try:
            # Payload baseado no original
            payload = self._build_payload_for_hotel(int(hotel_id))
            
            print(f"📡 Fazendo requisição para TripAdvisor...")
            
            # Faz a requisição
            response = session.post(
                self.base_url,
                json=payload,
                timeout=self.timeout
            )
            
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                # Debug do tipo de conteúdo
                content_type = response.headers.get('content-type', 'unknown')
                content_encoding = response.headers.get('content-encoding', 'none')
                print(f"📋 Content-Type: {content_type}")
                print(f"📋 Content-Encoding: {content_encoding}")
                
                try:
                    # Força a descompressão se necessário
                    if content_encoding and content_encoding != 'none':
                        print(f"🔄 Descomprimindo conteúdo ({content_encoding})...")
                    
                    response_data = response.json()
                    print(f"✅ JSON válido recebido ({len(response_data)} items)")
                    
                    # Extrai dados de rating
                    rating_data = self._extract_rating_data(response_data)
                    
                    if rating_data:
                        print(f"✅ Dados extraídos: Rating {rating_data['rating']}/5.0, {rating_data['review_count']} avaliações")
                        
                        return {
                            "hotel_id": hotel_id,
                            "hotel_name": hotel_name,
                            "hotel_url": hotel_url,
                            "rating": float(rating_data['rating']),
                            "review_count": int(rating_data['review_count']),
                            "source": "tripadvisor_realtime",
                            "data_source": rating_data['source'],
                            "extraction_timestamp": datetime.now().isoformat(),
                            "reviews": []  # Pode ser expandido depois
                        }
                    else:
                        print("❌ Dados de rating não encontrados na resposta")
                        # Debug: salva resposta para análise
                        with open(f"debug_response_{hotel_id}.json", "w") as f:
                            json.dump(response_data, f, indent=2)
                        print(f"💾 Resposta salva em debug_response_{hotel_id}.json")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Erro ao decodificar JSON: {e}")
                    # Debug melhorado
                    print(f"📋 Response length: {len(response.content)} bytes")
                    print(f"📋 Response text length: {len(response.text)} chars")
                    
                    # Tenta descomprimir manualmente
                    print("🔄 Tentando descompressão manual...")
                    try:
                        decompressed_text = self._try_decompress_content(response.content)
                        print(f"✅ Descompressão bem-sucedida! ({len(decompressed_text)} chars)")
                        
                        # Tenta fazer JSON com o conteúdo descomprimido
                        response_data = json.loads(decompressed_text)
                        print(f"✅ JSON válido após descompressão ({len(response_data)} items)")
                        
                        # Extrai dados de rating
                        rating_data = self._extract_rating_data(response_data)
                        
                        if rating_data:
                            print(f"✅ Dados extraídos: Rating {rating_data['rating']}/5.0, {rating_data['review_count']} avaliações")
                            
                            return {
                                "hotel_id": hotel_id,
                                "hotel_name": hotel_name,
                                "hotel_url": hotel_url,
                                "rating": float(rating_data['rating']),
                                "review_count": int(rating_data['review_count']),
                                "source": "tripadvisor_realtime",
                                "data_source": rating_data['source'],
                                "extraction_timestamp": datetime.now().isoformat(),
                                "reviews": []
                            }
                        else:
                            # Salva resposta descomprimida para debug
                            with open(f"debug_decompressed_{hotel_id}.json", "w") as f:
                                json.dump(response_data, f, indent=2)
                            print(f"💾 Resposta descomprimida salva em debug_decompressed_{hotel_id}.json")
                            
                    except Exception as decomp_error:
                        print(f"❌ Falha na descompressão manual: {decomp_error}")
                        print(f"Content preview: {response.text[:200]}...")
                        
                        # Salva conteúdo bruto para debug
                        debug_file = f"debug_raw_{hotel_id}.html"
                        with open(debug_file, "wb") as f:
                            f.write(response.content)
                        print(f"💾 Conteúdo bruto salvo em {debug_file}")
            else:
                print(f"❌ Status HTTP {response.status_code}")
                print(f"Response: {response.text[:200]}...")
        
        except Exception as e:
            print(f"❌ Erro na requisição: {e}")
        
        finally:
            session.close()
        
        return None
    
    def _extract_hotel_id(self, url: str) -> str:
        """Extrai ID do hotel da URL"""
        try:
            parts = url.split('-d')
            if len(parts) > 1:
                return parts[1].split('-')[0]
            return ""
        except:
            return ""
    
    def _try_decompress_content(self, content: bytes) -> str:
        """Tenta descomprimir conteúdo usando diferentes métodos"""
        try:
            # Tenta gzip
            return gzip.decompress(content).decode('utf-8')
        except:
            try:
                # Tenta zlib
                return zlib.decompress(content).decode('utf-8')
            except:
                try:
                    # Tenta deflate
                    return zlib.decompress(content, -15).decode('utf-8')
                except:
                    # Retorna como string normal
                    return content.decode('utf-8', errors='ignore')
    
    def scrape_multiple_hotels(self, hotels_config: Dict[str, str]) -> List[Dict[str, Any]]:
        """Scrapa múltiplos hotéis - estilo original"""
        results = []
        total_hotels = len(hotels_config)
        
        print(f"🚀 TRIPADVISOR SCRAPER - ESTILO ORIGINAL")
        print(f"🎯 Processando {total_hotels} hotéis")
        print("=" * 50)
        
        for i, (hotel_name, hotel_url) in enumerate(hotels_config.items(), 1):
            print(f"\n[{i}/{total_hotels}] {hotel_name}")
            
            hotel_data = self.scrape_hotel(hotel_url, hotel_name)
            
            if hotel_data:
                results.append(hotel_data)
                print(f"✅ Sucesso! ({len(results)} processados)")
            else:
                print(f"❌ Falha no hotel {i}")
            
            # Delay entre hotéis
            if i < total_hotels:
                delay = random.uniform(5, 10)
                print(f"⏳ Delay {delay:.1f}s...")
                time.sleep(delay)
        
        print(f"\n🎯 CONCLUÍDO: {len(results)}/{total_hotels} hotéis")
        return results 