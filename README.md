# Agente de bate-papo empresarial configurável
Este Chat Agent foi desenvolvido especificamente como um aplicativo de exemplo reutilizável e configurável para compartilhar com empresas ou clientes potenciais.

1. Ele usa [LangChain](https://www.langchain.com/) como estrutura para configurar facilmente cadeias de perguntas e respostas do LLM
2. Ele usa [Streamlit](https://streamlit.io/) como estrutura para criar facilmente aplicativos da Web
3. Ele usa [Astra DB](https://astra.datastax.com/) como armazenamento de vetores para permitir o Retrieval Augmented Generation, a fim de fornecer interações contextuais significativas
4. Ele usa [Astra DB](https://astra.datastax.com/) como memória de curto prazo para acompanhar o que foi dito e gerado
5. Ele usa um StreamingCallbackHandler para transmitir a saída para a tela, o que evita ter que esperar pela resposta final
6. Ele permite que novo conteúdo seja carregado, vetorizado e armazenado no banco de dados vetorial Astra DB para que possa ser usado como contexto
7. Oferece uma localização configurável através de `localization.csv`
8. Oferece uma experiência guiada sobre trilhos através de `rails.csv`

## Preparação
1. Primeiro instale as dependências do Python usando:
```
pip3 install -r requirements.txt
```
2. Em seguida, atualize os segredos `OpenAI`, `AstraDB` e opcionalmente `LangSmith` em `streamlit-langchain/.streamlit/secrets.toml`. Há um exemplo fornecido em `secrets.toml.example`.

## Personalização

Agora é hora de personalizar o aplicativo para seu caso específico.

### Passo 1
Defina as credenciais adicionando um novo nome de usuário e senha na seção `[passwords]` em `streamlit-langchain/.streamlit/secrets.toml`.
### Passo 2
Defina o idioma da UI do aplicativo adicionando um código de localização na seção `[languages]` em `streamlit-langchain/.streamlit/secrets.toml`. Atualmente `en_US`, `nl_NL` e `pt_BR` são suportados. No entanto, é fácil adicionar idiomas adicionais em `localization.csv`.
### Etapa 3
Crie uma experiência guiada fornecendo exemplos de prompts em `rails.csv`. A convenção aqui é que `<username>` da Etapa 1 seja usado para definir a experiência.
### Passo 4
Inicie o aplicativo e carregue previamente os arquivos PDF e de texto relevantes para que o aplicativo tenha conteúdo que possa ser usado como contexto para as perguntas/solicitações na próxima etapa. Todos esses dados serão carregados em uma tabela específica do usuário definida por `<username>`.
### Etapa 5
Crie uma página de boas-vindas personalizada na pasta raiz. A convenção aqui é criar um arquivo markdown chamado `<username>.md`. O ideal é listar quais arquivos foram pré-carregados.

## Começando
Você está pronto para executar o aplicativo da seguinte maneira:
```
streamlit run app.py
```
Além do conteúdo pré-carregado, um usuário pode adicionar conteúdo adicional que será usado como contexto para prompts.

## Implante na Internet
É fácil enviar este aplicativo para a edição comunitária do Streamlit. Como o aplicativo usa uma página de login, é seguro disponibilizá-la publicamente.

## Aviso
O objetivo deste aplicativo é ser facilmente compartilhado dentro das empresas. Esteja ciente de que SUA assinatura OPENAI está sendo usada para criar embeddings e chamadas LLM. Isso IRÁ incorrer em custos.