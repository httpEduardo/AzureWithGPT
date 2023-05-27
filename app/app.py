import os
import logging
import openai
from flask import Flask, request, jsonify
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from approaches.chatreadretrieveread import ChatReadRetrieveReadApproach

# Replace these with your own values, either in environment variables or directly here
AZURE_STORAGE_ACCOUNT = os.environ.get("AZURE_STORAGE_ACCOUNT") or "mystorageaccount"
AZURE_STORAGE_CONTAINER = os.environ.get("AZURE_STORAGE_CONTAINER") or "content"

AZURE_SEARCH_SERVICE = os.environ.get("AZURE_SEARCH_SERVICE") or "gptkb"
AZURE_SEARCH_INDEX = os.environ.get("AZURE_SEARCH_INDEX") or "gptkbindex"
AZURE_SEARCH_KEY = os.environ.get("AZURE_SEARCH_KEY") or "gptkbkey"
AZURE_SEARCH_SEMANTIC = os.environ.get("AZURE_SEARCH_KEY") or "gptkbsemantic"

OPENAI_KEY = os.environ.get("OPENAI_KEY") or ""

KB_FIELDS_CONTENT = os.environ.get("KB_FIELDS_CONTENT") or "content"
KB_FIELDS_CATEGORY = os.environ.get("KB_FIELDS_CATEGORY") or "category"
KB_FIELDS_SOURCEPAGE = os.environ.get("KB_FIELDS_SOURCEPAGE") or "sourcepage"

openai.api_key = f"{OPENAI_KEY}"

# Set up clients for Cognitive Search and Storage
search_client = SearchClient(
    endpoint=f"https://{AZURE_SEARCH_SERVICE}.search.windows.net/",
    index_name=AZURE_SEARCH_INDEX,
    credential=AzureKeyCredential(AZURE_SEARCH_KEY))

chat_approaches = {
    "rrr": ChatReadRetrieveReadApproach(search_client, 
                                        KB_FIELDS_SOURCEPAGE,
                                        KB_FIELDS_CONTENT,
                                        AZURE_SEARCH_SEMANTIC)
}

app = Flask(__name__)

@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def static_file(path):
    return app.send_static_file(path)

# Chamada CURL /chat
# curl --location "http://127.0.0.1:5000/chat" 
#      --header "Content-Type: application/json" 
#      --data "{\"history\":[{\"user\":\"TEXTO USUARIO\",\"bot\":\"HISTORICO BOT\"}],
#               \"approach\":\"rrr\",\"overrriders\":{\"semantic_ranker\":\"true\"}}"
# 
@app.route("/chat", methods=["POST"])
def chat():
    ensure_openai_token()
    approach = request.json["approach"]
    impl = chat_approaches.get(approach)
    try:
        if not impl:
            return jsonify({"error": "unknown approach"}), 400
        r = impl.run(request.json["history"], request.json.get("overrides") or {})
        return jsonify(r)
    except Exception as e:
        logging.exception("Exception in /chat")
        return jsonify({"error": str(e)}), 500

def ensure_openai_token():
    global openai_token
    openai.api_key = f"{OPENAI_KEY}"
    
if __name__ == "__main__":
    app.run()
