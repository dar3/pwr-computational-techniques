import random

CLASSES = [

    ("Grupa_1", "Matematyka"), ("Grupa_1", "Matematyka"), ("Grupa_1", "Fizyka"),
    ("Grupa_1", "Informatyka"), ("Grupa_1", "j.polski"), ("Grupa_1", "j.polski"),
    ("Grupa_1", "j.angielski"), ("Grupa_1", "j.angielski"), ("Grupa_1", "biologia"),
    ("Grupa_1", "geografia"), ("Grupa_1", "muzyka"), ("Grupa_1", "WF"),
    ("Grupa_1", "WF"), ("Grupa_1", "EDB"), ("Grupa_1", "historia"),


    ("Grupa_2", "Matematyka"), ("Grupa_2", "Matematyka"), ("Grupa_2", "Sieci"),
    ("Grupa_2", "Sieci"), ("Grupa_2", "Bazy danych"), ("Grupa_2", "Bazy danych"),
    ("Grupa_2", "j.niemiecki"), ("Grupa_2", "chemia"), ("Grupa_2", "biologia"),
    ("Grupa_2", "WOS"), ("Grupa_2", "muzyka"), ("Grupa_2", "WF"),
    ("Grupa_2", "WF"), ("Grupa_2", "EDB"), ("Grupa_2", "j.angielski"),


    ("Grupa_3", "Matematyka"), ("Grupa_3", "Matematyka"), ("Grupa_3", "Elektrotechnika"),
    ("Grupa_3", "Elektrotechnika"), ("Grupa_3", "Pomiary"), ("Grupa_3", "j.polski"),
    ("Grupa_3", "j.polski"), ("Grupa_3", "j.angielski"), ("Grupa_3", "j.angielski"),
    ("Grupa_3", "historia"), ("Grupa_3", "WF"), ("Grupa_3", "WF"),
    ("Grupa_3", "fizyka"), ("Grupa_3", "chemia"), ("Grupa_3", "EDB"),
]

ROOMS = ["Sala_A", "Sala_B","Sala_C", "Sala_D", "Sala_E", "Sala_F", "Sala_G", "Sala_H", "Sala_I", "Sala_J"]
TIMESLOTS = range(40)
SLOTS_PER_DAY = 8


# create chromosome
# vector representation of the same length
# gen (time, room)
def create_individual():
    return [(random.choice(TIMESLOTS), random.choice(ROOMS)) for _ in CLASSES]


def calculate_fitness(individual):
    score = 1000
    room_time_map = set()
    group_time_map = set()
    group_daily_slots = {group: {} for group, _ in CLASSES}

    for i, (time, room) in enumerate(individual):
        group = CLASSES[i][0]

        # cannot be two groups in the same room at the same time
        if (time, room) in room_time_map:
            score -= 100
        else:
            room_time_map.add((time, room))


        # limitation group cannot be in the two diff rooms at the same time
        if (time, group) in group_time_map:
            score -= 100
        else:
            group_time_map.add((time, group))

        # coll data for big breaks
        day = time // SLOTS_PER_DAY
        slot = time % SLOTS_PER_DAY
        if day not in group_daily_slots[group]:
            group_daily_slots[group][day] = []
        group_daily_slots[group][day].append(slot)

    # 5 day
    for group, days in group_daily_slots.items():
        if len(days) < 5:

            score -= 100 * (5 - len(days))

        for day, slots in days.items():
            if len(slots) > 1:
                slots.sort()
                # getting rid of big breaks
                spread = slots[-1] - slots[0] + 1
                gaps = spread - len(slots)
                if gaps > 0:
                    score -= 10 * gaps

            MAX_CLASSES_PER_DAY = 3
            if len(slots) > MAX_CLASSES_PER_DAY:
                # minus 100 points for each lesson above limit (to make lessons on 5 day)
                score -= 100 * (len(slots) - MAX_CLASSES_PER_DAY)
    return max(score, 0)


# random 3 and choose the best
# genetic diversity vs roulette
def tournament_selection(population, fitnesses, k=3):
    selected_indices = random.sample(range(len(population)), k)
    best_index = max(selected_indices, key=lambda i: fitnesses[i])
    return population[best_index]

# parents chromosome cut in random place and changed
def single_point_crossover(parent1, parent2, crossover_rate):
    if random.random() < crossover_rate:
        point = random.randint(1, len(CLASSES) - 1)
        child1 = parent1[:point] + parent2[point:]
        child2 = parent2[:point] + parent1[point:]
        return child1, child2
    return parent1[:], parent2[:]


def mutate(individual, mutation_rate):
    for i in range(len(individual)):
        if random.random() < mutation_rate:
            individual[i] = (random.choice(TIMESLOTS), random.choice(ROOMS))
    return individual

def print_schedule(individual):

    # mapping one-dim chromosome back to visible table

    # Initializing empty schedule for each group for each day
    num_days = len(TIMESLOTS) // SLOTS_PER_DAY
    schedule = {}
    for group, _ in CLASSES:
        if group not in schedule:
            schedule[group] = {day: {} for day in range(num_days)}

    # filling schedule
    for i, (time, room) in enumerate(individual):
        group, subject = CLASSES[i]
        day = time // SLOTS_PER_DAY
        slot = time % SLOTS_PER_DAY

        display_text = f"{subject[:10]} ({room[-1]})"

        # possible conflicts
        if slot in schedule[group][day]:
            schedule[group][day][slot] += f" / CONFLICT"
        else:
            schedule[group][day][slot] = display_text

    header_days = " | ".join([f"Dzień {d + 1:<14}" for d in range(num_days)])
    line_len = 9 + len(header_days)

    print("\n" + "=" * line_len)
    print(f"{'Final schedule':^{line_len}}")
    print("=" * line_len)

    for group, days in sorted(schedule.items()):
        print(f"\n{group.upper():^{line_len}}")
        print("-" * line_len)
        print(f"{'Slot':<6} | {header_days}")
        print("-" * line_len)

        for slot in range(SLOTS_PER_DAY):
            row_classes = []
            for d in range(num_days):
                row_classes.append(f"{days[d].get(slot, '---'):<14}")

            row_str = " | ".join(row_classes)
            print(f"Slot {slot:<1} | {row_str}")

def run_genetic_algorithm(pop_size, generations, crossover_rate, mutation_rate):
    population = [create_individual() for _ in range(pop_size)]

    best_fitness_history = []

    for generation in range(generations):
        fitnesses = [calculate_fitness(ind) for ind in population]
        best_fitness_history.append(max(fitnesses))

        # stop criteria
        if max(fitnesses) == 1000:
            break

        new_population = []
        while len(new_population) < pop_size:
            # selection
            p1 = tournament_selection(population, fitnesses)
            p2 = tournament_selection(population, fitnesses)

            # crossing
            c1, c2 = single_point_crossover(p1, p2, crossover_rate)

            # mutation
            c1 = mutate(c1, mutation_rate)
            c2 = mutate(c2, mutation_rate)

            new_population.extend([c1, c2])

        population = new_population[:pop_size]  # rejection of any excess individual

    final_fitnesses = [calculate_fitness(ind) for ind in population]
    best_ind = population[final_fitnesses.index(max(final_fitnesses))]
    return best_ind, max(final_fitnesses), generation + 1


print(f"Ilosc zajec do zaplanowania: {len(CLASSES)}\n")
# pop how many schedules to analyze at once
# gen more gen more iter of improv
# cx_pb exploatation
#  mut_pb exploration
experiments = [
    # Baseline (2 lessons random modified)
    {"pop": 800, "gen": 1000, "cx_pb": 0.8, "mut_pb": 0.05},
    # Agressive exploration (mutation destroys) random change 4.5 gens
    {"pop": 900, "gen": 1500, "cx_pb": 0.9, "mut_pb": 0.1},
    # slow learning mainly based on pop. low mut  and cross
    {"pop": 900, "gen": 1000, "cx_pb": 0.3, "mut_pb": 0.01},
]

for i, params in enumerate(experiments, 1):
    best_solution, best_score, gens = run_genetic_algorithm(
        pop_size=params["pop"],
        generations=params["gen"],
        crossover_rate=params["cx_pb"],
        mutation_rate=params["mut_pb"]
    )
    print(f"Eksperyment {i}: [Pop: {params['pop']}, Cx: {params['cx_pb']}, Mut: {params['mut_pb']}]")
    print(f"Najlepszy fitness: {best_score}/1000 (Osiągnięto w generacji {gens})")
    print("-" * 40)

print("\n Plan zajęć dla najelpszego rozwiązania")
print_schedule(best_solution)