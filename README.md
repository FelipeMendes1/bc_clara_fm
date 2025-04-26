# E-commerce Funnel Analysis Tool

## Descrição do Projeto
Ferramenta de análise de funil de conversão de e-commerce para identificar problemas de conversão e fornecer recomendações estratégicas para melhorias.

## Estrutura do Funil
O site de e-commerce analisado possui uma estrutura simples de 4 páginas:
1. **Página inicial (Home)** - Ponto de entrada para todos os usuários
2. **Página de pesquisa (Search)** - Usuários chegam aqui após realizar uma pesquisa na página inicial
3. **Página de pagamento (Payment)** - Usuários chegam aqui após clicar em um produto na página de pesquisa
4. **Página de confirmação (Confirmation)** - Usuários chegam aqui após completar o pagamento

## Funcionalidades da Ferramenta
- Análise completa do funil de conversão
- Segmentação por dispositivo (Desktop vs Mobile)
- Segmentação por gênero
- Comparação entre usuários novos e existentes
- Identificação de pontos de abandono críticos
- Geração de insights baseados nos dados
- Recomendações estratégicas para melhorias
- Exportação de apresentação em PowerPoint

## Tecnologias Utilizadas
- Python
- Pandas para análise de dados
- Streamlit para a interface web
- Plotly para visualizações interativas
- Python-pptx para geração de apresentações

## Como Executar
1. Clone este repositório
2. Instale as dependências: `pip install -r requirements.txt`
3. Execute o aplicativo: `streamlit run app.py`

## Estrutura de Arquivos
- `app.py` - Aplicativo Streamlit principal
- `utils.py` - Funções utilitárias para carregamento e processamento de dados
- `analysis.py` - Funções para análise do funil e geração de insights
- `visualization.py` - Funções para criação de visualizações
- `presentation.py` - Funções para geração de apresentações PowerPoint
- `attached_assets/` - Diretório contendo os arquivos CSV de dados

## Análise de Dados
- **Conversão geral** - Taxa de conversão da página inicial até a confirmação
- **Pontos de abandono** - Identificação de onde os usuários abandonam o funil
- **Diferenças por segmento** - Comparação de desempenho entre segmentos de usuários
- **Foco em usuários novos** - Análise específica do comportamento de novos usuários
