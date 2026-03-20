#!/bin/bash
# Script de test de l'API — Étape 07
# Usage: bash test_api.sh

BASE_URL=${API_URL:-"http://localhost:8000"}
SESSION="test-session-$(date +%s)"

echo "=== Test de l'API Chatbot — Étape 07 ==="
echo "URL: $BASE_URL"
echo "Session: $SESSION"
echo ""

# Test 1: Health check
echo "--- Test 1: GET /health ---"
curl -s "$BASE_URL/health" | python3 -m json.tool
echo ""

# Test 2: Premier message
echo "--- Test 2: POST /chat (premier message) ---"
curl -s -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Bonjour ! Je m'appelle Alice.\", \"session_id\": \"$SESSION\"}" \
  | python3 -m json.tool
echo ""

# Test 3: Message de suivi (test mémoire)
echo "--- Test 3: POST /chat (test mémoire) ---"
curl -s -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Comment je m'appelle ?\", \"session_id\": \"$SESSION\"}" \
  | python3 -m json.tool
echo ""

# Test 4: Historique
echo "--- Test 4: GET /history/$SESSION ---"
curl -s "$BASE_URL/history/$SESSION" | python3 -m json.tool
echo ""

# Test 5: Sessions
echo "--- Test 5: GET /sessions ---"
curl -s "$BASE_URL/sessions" | python3 -m json.tool
echo ""

echo "=== Tests terminés ==="
