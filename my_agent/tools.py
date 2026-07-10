"""
Outils disponibles pour l'agent de test.
Ajoute ici tes propres fonctions Python pour étendre les capacités de l'agent.
"""


def get_current_time() -> dict:
    """Retourne la date et l'heure actuelles (UTC)."""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    return {
        "datetime_utc": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
    }


def calculator(expression: str) -> dict:
    """
    Évalue une expression mathématique simple et retourne le résultat.

    Args:
        expression: Expression mathématique à évaluer (ex: "2 + 2", "10 * 5 / 2").

    Returns:
        Un dictionnaire contenant le résultat ou un message d'erreur.
    """
    import ast
    import operator

    # Opérateurs autorisés (pas d'exec/eval dangereux)
    allowed_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }

    def _eval(node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in allowed_operators:
                raise ValueError(f"Opérateur non autorisé : {op_type}")
            return allowed_operators[op_type](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -_eval(node.operand)
        else:
            raise ValueError(f"Type de nœud non supporté : {type(node)}")

    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval(tree.body)
        return {"expression": expression, "result": result, "status": "ok"}
    except Exception as e:
        return {"expression": expression, "error": str(e), "status": "error"}
