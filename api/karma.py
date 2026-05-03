# Proof-of-Karma API
# Эндпоинты /api/karma и /api/top

karma_scores = {"KARMA_ARCHITECT": 300}

def get_karma(address):
    return karma_scores.get(address, 0)

def get_top(n=10):
    sorted_karma = sorted(karma_scores.items(), key=lambda x: x[1], reverse=True)
    return [{"address": a, "karma": k} for a, k in sorted_karma[:n]]

def update_karma(address, action_type):
    if address not in karma_scores:
        karma_scores[address] = 0
    if action_type == "creation":
        karma_scores[address] += 3
    elif action_type == "spam":
        karma_scores[address] -= 5
