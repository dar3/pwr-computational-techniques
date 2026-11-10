import random
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


x = [0, 3, 6, 7, 15, 10, 16, 5, 8, 1.5]
y = [1, 2, 1, 4.5, -1, 2.5, 11, 6, 9, 12]
CITIES = ["Wrocław", "Łódź", "Kraków", "Kielce", "Mielec",
          "Rzeszów", "Białystok", "Poznań", "Bydgoszcz", "Szczecin"]
N = len(CITIES)

# eucl distance
def distance(a, b):
    return ((x[a] - x[b]) ** 2 + (y[a] - y[b]) ** 2) ** 0.5


def route_length(route):
    total = 0
    for i in range(N):
        total += distance(route[i], route[(i + 1) % N])  # % N coming back to start city
    return total


def fitness(route):
    return 1 / route_length(route)


# each function choose one parent
def sel_roulette(population):
    weights = [fitness(ind) for ind in population]
    # debugging
    # print(random.choices(population, weights=weights, k=1)[0], "with weight:" , weights)
    return random.choices(population, weights=weights, k=1)[0]


def sel_tournament(population, size=3):
    competitors = random.sample(population, size)
    return min(competitors, key=route_length)


def sel_elite(population, elite_fraction=0.2):
    elite_count = max(1, int(len(population) * elite_fraction))
    elite_population = sorted(population, key=route_length)[:elite_count]
    return random.choice(elite_population)


def crossover(parent1, parent2):
    cut = random.randint(1, N - 1)
    child1 = parent1[:cut] + [c for c in parent2 if c not in parent1[:cut]]
    child2 = parent2[:cut] + [c for c in parent1 if c not in parent2[:cut]]
    return child1, child2


def mut_swap(route):
    route = route[:]
    i, j = random.sample(range(N), 2)
    route[i], route[j] = route[j], route[i]
    return route


def mut_insertion(route):
    route = route[:]
    i, j = random.sample(range(N), 2)
    city = route.pop(i)
    route.insert(j, city)
    return route


def mut_scramble(route):
    route = route[:]
    i, j = sorted(random.sample(range(N), 2))
    part = route[i:j + 1]
    random.shuffle(part)
    route[i:j + 1] = part
    return route


def inver(route):
    route = route[:]
    i, j = sorted(random.sample(range(N), 2))
    route[i:j + 1] = route[i:j + 1][::-1]
    return route


SELECTIONS = {"ruletka": sel_roulette, "turniejowa": sel_tournament,
              "elitarna": sel_elite}
MUTATIONS = {"zamiana": mut_swap, "wstawienie": mut_insertion,
             "przemieszanie": mut_scramble}


def run_ga(selection, mutation, p_inv, pop_size=20, n_generations=50, pc=0.8, pm=0.1):
# def run_ga(selection, mutation, p_inv, pop_size=20, n_generations=50, pc=0.8, pm=0.8):
    select = SELECTIONS[selection]
    mutate = MUTATIONS[mutation]

    population = [random.sample(range(N), N) for _ in range(pop_size)]

    # debugging
    # print(population)

    # best overall
    best_route = min(population, key=route_length)
    history = []

    for _ in range(n_generations):          # stop num of generations
        gen_best = min(population, key=route_length)
        if route_length(gen_best) < route_length(best_route):
            best_route = gen_best
        history.append(route_length(best_route))

        # creating new generation
        new_population = []
        if selection == "elitarna":
            # copy best indv to new gener
            new_population.append(min(population, key=route_length)[:])
        while len(new_population) < pop_size:
            parent1 = select(population)
            parent2 = select(population)

            if random.random() < pc:                    # crossing (ran 0-1 excl)
                child1, child2 = crossover(parent1, parent2)
            else:
                child1, child2 = parent1[:], parent2[:]

            for child in (child1, child2):
                if random.random() < pm:                # mut
                    child = mutate(child)
                if random.random() < p_inv:             # inv
                    child = inver(child)
                new_population.append(child)
        population = new_population[:pop_size]

    # check last gen again
    gen_best = min(population, key=route_length)
    if route_length(gen_best) < route_length(best_route):
        best_route = gen_best
    history.append(route_length(best_route))
    return route_length(best_route), best_route, history


N_TRIALS = 20
INV_VALUES = [0.0, 0.1]   # no inv / inv 10%


def run_all():
    results = []
    # avg his converg
    histories = {}
    runs = {}

    for sel in SELECTIONS:
        for mut in MUTATIONS:
            for p_inv in INV_VALUES:
                name = f"{sel} + {mut} + inw={p_inv}"
                lengths, hists = [], []
                for trial in range(N_TRIALS):
                    random.seed(trial)
                    length, _, hist = run_ga(sel, mut, p_inv)
                    lengths.append(length)
                    hists.append(hist)
                results.append({"selekcja": sel, "mutacja": mut, "inwersja": p_inv,
                                "średnia": np.mean(lengths), "odch. std": np.std(lengths),
                                "najlepszy": min(lengths), "najgorszy": max(lengths),
                                "nazwa": name})
                # avg best for each gen
                histories[name] = np.mean(hists, axis=0)
                runs[name] = lengths

    # dict to table
    table = pd.DataFrame(results).sort_values("średnia").reset_index(drop=True)
    table.index += 1
    return table, histories, runs


def show_table(table):
    print("\nWyniki")
    print(table.drop(columns=["nazwa"]).round(3).to_string())


def show_best(table):
    best = table.iloc[0]
    print("\n Najlepsza konfiguracja (najmniejsza średnia długość trasy):")
    print(f"  selekcja : {best['selekcja']}")
    print(f"  mutacja  : {best['mutacja']}")
    print(f"  inwersja : {best['inwersja']}")
    print(f"  średnia długość trasy: {best['średnia']:.3f} (najlepszy wynik: {best['najlepszy']:.3f})")


def show_converg(table, histories):
    plt.figure(figsize=(8, 5))
    plt.plot(histories[table.iloc[0]["nazwa"]], label="najlepsza: " + table.iloc[0]["nazwa"])
    plt.plot(histories[table.iloc[-1]["nazwa"]], label="najgorsza: " + table.iloc[-1]["nazwa"])
    plt.xlabel("Pokolenie")
    plt.ylabel("Najlepsza dotychczasowa długość trasy (średnia)")
    plt.title("Zbieżność algorytmu")
    plt.legend(fontsize=8)
    plt.show()


def show_route(route):
    r = route + [route[0]]
    plt.figure(figsize=(7, 6))
    plt.plot([x[i] for i in r], [y[i] for i in r], "-o")
    for i, name in enumerate(CITIES):
        plt.annotate(name, (x[i], y[i]))
    plt.title(f"Najlepsza trasa, długość = {route_length(route):.2f}")
    plt.show()

if __name__ == "__main__":
    table, histories, runs = run_all()
    show_table(table)
    show_best(table)
    show_converg(table, histories)
    best = table.iloc[0]
    random.seed(0)
    _, route, _ = run_ga(best["selekcja"], best["mutacja"], best["inwersja"])
    show_route(route)
