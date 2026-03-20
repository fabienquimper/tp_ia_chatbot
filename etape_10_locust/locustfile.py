"""
Étape 10 — Test de charge avec Locust
Simule des utilisateurs réels envoyant des messages au chatbot.

Usage :
  locust -f locustfile.py --host=http://localhost:8000
  locust -f locustfile.py --host=http://localhost:8000 --headless --users 50 --spawn-rate 5 --run-time 2m --csv=results
"""
import random, uuid
from locust import HttpUser, task, between, events

# Chargement des prompts depuis le fichier
def load_prompts(filepath="prompts.txt"):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        return lines if lines else ["Bonjour, comment vas-tu ?"]
    except FileNotFoundError:
        return [
            "Explique le RAG en 2 phrases.",
            "Qu'est-ce qu'un LLM ?",
            "Donne-moi un exemple de prompt engineering.",
        ]

PROMPTS = load_prompts()

class ChatUser(HttpUser):
    """
    Simule un utilisateur réel qui :
    - Envoie des messages au chatbot
    - Vérifie sa santé périodiquement
    - Consulte son historique occasionnellement
    """
    wait_time = between(1, 3)  # Pause réaliste entre les actions

    def on_start(self):
        """Initialise la session de l'utilisateur."""
        self.session_id = f"locust-{uuid.uuid4().hex[:8]}"
        self.message_count = 0

    @task(5)  # Tâche principale (poids 5 = 5x plus fréquente)
    def send_message(self):
        """Envoie un message aléatoire."""
        prompt = random.choice(PROMPTS)
        with self.client.post(
            "/chat",
            json={"message": prompt, "session_id": self.session_id},
            catch_response=True,
            name="/chat"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "reply" not in data:
                    response.failure("Réponse sans 'reply'")
                else:
                    self.message_count += 1
                    response.success()
            elif response.status_code == 429:
                response.failure("Rate limit (429)")
            elif response.status_code == 503:
                response.failure("LLM indisponible (503)")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(3)  # Health check (poids 3)
    def health_check(self):
        """Vérifie la santé de l'API."""
        with self.client.get("/health", catch_response=True, name="/health") as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") != "ok":
                    response.failure("Status != ok")
                else:
                    response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)  # Consultation historique (poids 1 = rare)
    def get_history(self):
        """Consulte l'historique de la session."""
        with self.client.get(
            f"/history/{self.session_id}",
            catch_response=True,
            name="/history"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

    def on_stop(self):
        """Nettoyage en fin de test."""
        pass

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print(f"\n=== Démarrage du test de charge ===")
    print(f"Prompts chargés : {len(PROMPTS)}")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print(f"\n=== Test de charge terminé ===")
    stats = environment.stats
    total = stats.total
    print(f"Requêtes totales : {total.num_requests}")
    print(f"Échecs           : {total.num_failures}")
    if total.num_requests > 0:
        print(f"Taux d'échec     : {total.num_failures/total.num_requests*100:.1f}%")
    print(f"Latence moyenne  : {total.avg_response_time:.0f}ms")
    print(f"Latence P95      : {total.get_response_time_percentile(0.95):.0f}ms")
