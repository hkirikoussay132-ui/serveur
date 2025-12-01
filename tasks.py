# server/tasks.py
import json
import threading
from typing import List, Dict, Optional

class Tache:
    def __init__(self, id: int, titre: str, description: str, statut: str = "TODO", auteur: Optional[str]=None):
        self.id = id
        self.titre = titre
        self.description = description
        self.statut = statut  # TODO / DOING / DONE
        self.auteur = auteur

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "titre": self.titre,
            "description": self.description,
            "statut": self.statut,
            "auteur": self.auteur
        }

    @staticmethod
    def from_dict(d: Dict):
        return Tache(d["id"], d["titre"], d.get("description",""), d.get("statut","TODO"), d.get("auteur"))

class GestionnaireTaches:
    def __init__(self, persistence_file: Optional[str] = "tasks.json"):
        self._lock = threading.Lock()
        self._tasks: Dict[int, Tache] = {}
        self._next_id = 1
        self.persistence_file = persistence_file
        if persistence_file:
            self.load()

    def _update_next_id(self):
        if self._tasks:
            self._next_id = max(self._tasks.keys()) + 1
        else:
            self._next_id = 1

    def ajouter_tache(self, titre: str, description: str, auteur: Optional[str]=None) -> Tache:
        with self._lock:
            tid = self._next_id
            t = Tache(tid, titre, description, "TODO", auteur)
            self._tasks[tid] = t
            self._next_id += 1
            self.save()
            return t

    def supprimer_tache(self, id: int) -> bool:
        with self._lock:
            if id in self._tasks:
                del self._tasks[id]
                self.save()
                return True
            return False

    def lister_taches(self, filtre_statut: Optional[str]=None, filtre_auteur: Optional[str]=None) -> List[Dict]:
        with self._lock:
            tasks = list(self._tasks.values())
            if filtre_statut:
                tasks = [t for t in tasks if t.statut == filtre_statut]
            if filtre_auteur:
                tasks = [t for t in tasks if t.auteur == filtre_auteur]
            return [t.to_dict() for t in sorted(tasks, key=lambda x: x.id)]

    def changer_statut(self, id: int, statut: str) -> bool:
        with self._lock:
            if id in self._tasks:
                self._tasks[id].statut = statut
                self.save()
                return True
            return False

    def sauvegarder_manuel(self) -> None:
        self.save()

    def save(self):
        if not self.persistence_file:
            return
        with self._lock:
            dump = {
                "next_id": self._next_id,
                "tasks": [t.to_dict() for t in self._tasks.values()]
            }
            with open(self.persistence_file, "w", encoding="utf-8") as f:
                json.dump(dump, f, ensure_ascii=False, indent=2)

    def load(self):
        try:
            with open(self.persistence_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                tasks = data.get("tasks", [])
                self._tasks = {t["id"]: Tache.from_dict(t) for t in tasks}
                self._next_id = data.get("next_id", None) or 1
                self._update_next_id()
        except FileNotFoundError:
            self._tasks = {}
            self._next_id = 1
        except Exception as e:
            print("Erreur chargement tâches :", e)
            self._tasks = {}
            self._next_id = 1
