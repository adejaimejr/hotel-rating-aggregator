#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hotel Rating Aggregator
=======================

Main orchestrator that manages scrapers for multiple hotel sites:
- TripAdvisor (fully functional)
- Booking.com (fully functional)
- Google Travel (in development) 
- Decolar (fully functional)

Each site generates its own JSON file with structured data.
"""

import os
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional

# Importar scrapers de cada site
from sites.tripadvisor.scraper import TripAdvisorScraper
from sites.booking.scraper import BookingScraper
from sites.google.scraper import GoogleTravelScraper
from sites.decolar.scraper import DecolarScraper


class HotelScrapingOrchestrator:
    """Orquestrador principal do sistema de scraping multi-sites"""
    
    def __init__(self, config_file: str = "config.env"):
        """
        Inicializa o orquestrador
        
        Args:
            config_file: Caminho para o arquivo de configuração
        """
        self.config_file = config_file
        self.config = self._load_config()
        self.scrapers = self._initialize_scrapers()
        
    def _load_config(self) -> Dict[str, str]:
        """Carrega configurações do arquivo .env"""
        config = {}
        
        if not os.path.exists(self.config_file):
            print(f"❌ Arquivo de configuração não encontrado: {self.config_file}")
            return config
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
                        
            print(f"✅ Configurações carregadas: {len(config)} variáveis")
            return config
            
        except Exception as e:
            print(f"❌ Erro ao carregar configurações: {e}")
            return {}
    
    def _initialize_scrapers(self) -> Dict[str, Any]:
        """Inicializa scrapers para todos os sites"""
        return {
            'tripadvisor': TripAdvisorScraper(),
            'booking': BookingScraper(),
            'google': GoogleTravelScraper(),
            'decolar': DecolarScraper()
        }
    
    def _get_hotels_config_for_site(self, site: str) -> Dict[str, str]:
        """
        Extrai configuração de hotéis para um site específico
        
        Args:
            site: Nome do site (tripadvisor, booking, google, decolar)
            
        Returns:
            Dict com {nome_hotel: url_hotel}
        """
        hotels_config = {}
        site_upper = site.upper()
        
        # Busca dinamicamente todos os hotéis configurados para o site
        # Padrão: SITE_HOTEL_NAME=url
        for key, value in self.config.items():
            if key.startswith(f"{site_upper}_") and not key.endswith("_ID"):
                # Extrai o nome do hotel da chave de configuração
                hotel_key = key.replace(f"{site_upper}_", "")
                
                # Converte o nome da chave para formato de exibição
                hotel_name = self._format_hotel_name(hotel_key)
                
                hotels_config[hotel_name] = value
        
        return hotels_config
    
    def _format_hotel_name(self, hotel_key: str) -> str:
        """
        Converte chave de configuração em nome de exibição do hotel
        
        Args:
            hotel_key: Chave do hotel (ex: MARAGOGI_BRISA_EXCLUSIVE)
            
        Returns:
            Nome formatado do hotel (ex: Maragogi Brisa Exclusive)
        """
        # Converte de UPPER_CASE para Title Case
        words = hotel_key.lower().replace('_', ' ').split()
        formatted_words = []
        
        for word in words:
            # Palavras especiais que ficam em minúsculo
            if word in ['de', 'da', 'do', 'das', 'dos', 'e']:
                formatted_words.append(word)
            else:
                formatted_words.append(word.capitalize())
        
        # Se não começar com "Hotel", adiciona se apropriado
        formatted_name = ' '.join(formatted_words)
        if not formatted_name.lower().startswith('hotel') and not any(formatted_name.lower().startswith(prefix) for prefix in ['maragogi', 'pousada', 'resort']):
            formatted_name = f"Hotel {formatted_name}"
        
        return formatted_name
    
    def _save_results_to_json(self, site: str, results: List[Dict[str, Any]]) -> str:
        """
        Salva resultados em arquivo JSON específico do site
        
        Args:
            site: Nome do site
            results: Lista com dados dos hotéis
            
        Returns:
            Caminho do arquivo salvo
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resultados/{site}_dados_{timestamp}.json"
        
        # Garante que a pasta existe
        os.makedirs("resultados", exist_ok=True)
        
        # Estrutura final do JSON
        output_data = {
            "metadata": {
                "site": site,
                "total_hoteis": len(results),
                "timestamp_extracao": datetime.now().isoformat(),
                "versao_scraper": "2.0.0-multi-site"
            },
            "hoteis": results
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Dados salvos: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Erro ao salvar arquivo: {e}")
            return ""
    
    def scrape_site(self, site: str) -> Optional[str]:
        """
        Executa scraping para um site específico
        
        Args:
            site: Nome do site a ser processado
            
        Returns:
            Caminho do arquivo JSON gerado ou None se erro
        """
        if site not in self.scrapers:
            print(f"❌ Site não suportado: {site}")
            return None
        
        print(f"\n🚀 Iniciando scraping do {site.upper()}")
        print("=" * 50)
        
        # Obtém configuração de hotéis para o site
        hotels_config = self._get_hotels_config_for_site(site)
        
        if not hotels_config:
            print(f"❌ Nenhum hotel configurado para {site}")
            return None
        
        print(f"🏨 Hotéis configurados para {site}: {len(hotels_config)}")
        
        # Executa scraping
        scraper = self.scrapers[site]
        results = scraper.scrape_multiple_hotels(hotels_config)
        
        if results:
            # Salva resultados
            json_file = self._save_results_to_json(site, results)
            print(f"✅ {site.upper()} concluído: {len(results)} hotéis processados")
            return json_file
        else:
            print(f"❌ Nenhum resultado obtido para {site}")
            return None
    
    def scrape_all_sites(self) -> Dict[str, str]:
        """
        Executa scraping para todos os sites configurados
        
        Returns:
            Dict com {site: caminho_arquivo_json}
        """
        results = {}
        available_sites = ['tripadvisor', 'booking', 'google', 'decolar']
        
        print("🎯 INICIANDO SCRAPING MULTI-SITE")
        print("=" * 60)
        print(f"Sites disponíveis: {', '.join(available_sites)}")
        print(f"Total de hotéis por site: {len(self._get_hotels_config_for_site('tripadvisor'))}")
        
        for site in available_sites:
            try:
                json_file = self.scrape_site(site)
                if json_file:
                    results[site] = json_file
                    
                # Pequena pausa entre sites
                if site != available_sites[-1]:  # Não espera no último
                    print(f"⏳ Pausa entre sites...")
                    import time
                    time.sleep(2)
                    
            except Exception as e:
                print(f"❌ Erro ao processar {site}: {e}")
                continue
        
        return results
    
    def show_status(self):
        """Mostra status das configurações e scrapers"""
        print("📊 STATUS DO SISTEMA")
        print("=" * 40)
        
        # Status das configurações
        print(f"📁 Arquivo de config: {self.config_file}")
        print(f"⚙️  Configurações carregadas: {len(self.config)}")
        
        # Status dos scrapers
        print(f"\n🤖 Scrapers disponíveis:")
        for site, scraper in self.scrapers.items():
            implemented = getattr(scraper, 'implemented', True)
            status = "✅ Funcional" if implemented else "🚧 Em desenvolvimento"
            print(f"   {site.capitalize()}: {status}")
        
        # Status dos hotéis configurados
        print(f"\n🏨 Hotéis configurados por site:")
        for site in self.scrapers.keys():
            hotels = self._get_hotels_config_for_site(site)
            print(f"   {site.capitalize()}: {len(hotels)} hotéis")


def main():
    """Função principal com argumentos de linha de comando"""
    parser = argparse.ArgumentParser(
        description="Sistema Multi-Site de Scraping de Hotéis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py                    # Executa todos os sites
  python main.py --site tripadvisor # Executa apenas TripAdvisor
  python main.py --status           # Mostra status do sistema
  python main.py --sites booking decolar # Executa sites específicos
        """
    )
    
    parser.add_argument(
        '--site', 
        choices=['tripadvisor', 'booking', 'google', 'decolar'],
        help='Executa scraping para um site específico'
    )
    
    parser.add_argument(
        '--sites',
        nargs='+',
        choices=['tripadvisor', 'booking', 'google', 'decolar'],
        help='Executa scraping para múltiplos sites específicos'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Mostra status das configurações e scrapers'
    )
    
    parser.add_argument(
        '--config',
        default='config.env',
        help='Caminho para arquivo de configuração (padrão: config.env)'
    )
    
    args = parser.parse_args()
    
    # Inicializa orquestrador
    orchestrator = HotelScrapingOrchestrator(args.config)
    
    # Executa ação solicitada
    if args.status:
        orchestrator.show_status()
        
    elif args.site:
        # Executa site específico
        json_file = orchestrator.scrape_site(args.site)
        if json_file:
            print(f"\n🎯 Arquivo gerado: {json_file}")
            
    elif args.sites:
        # Executa múltiplos sites específicos
        results = {}
        for site in args.sites:
            json_file = orchestrator.scrape_site(site)
            if json_file:
                results[site] = json_file
        
        print(f"\n🎯 Arquivos gerados: {len(results)}")
        for site, file_path in results.items():
            print(f"   {site.capitalize()}: {file_path}")
            
    else:
        # Executa todos os sites (padrão)
        results = orchestrator.scrape_all_sites()
        
        print(f"\n🎯 SCRAPING CONCLUÍDO")
        print("=" * 30)
        print(f"Sites processados: {len(results)}")
        
        for site, file_path in results.items():
            print(f"✅ {site.capitalize()}: {file_path}")


if __name__ == "__main__":
    main() 