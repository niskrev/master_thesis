from LSTM import *
from collections import OrderedDict
from config import *
from sklearn.decomposition import PCA

plt.style.use("seaborn")


class GeneticAlgorithm:
    def __init__(
        self,
        training_set_ga,
        testing_set_ga,
        network_architecture=OrderedDict(
            [
                ("Layer1", [10, 21, 5]),
                ("Layer2", [2, 20, 5]),
                ("Layer3", [1, 21, 1]),
                ("Layer4", [0, 5, 1]),
            ]
        ),
        learning_rate=[0.0001, 0.1, 0.005],
        initial_population_source_external=False,
        build_grid_scenarios=True,
    ):
        self.training_set_ga = training_set_ga
        self.testing_set_ga = testing_set_ga
        self.network_architecture = network_architecture
        self.learning_rate = learning_rate
        self.initial_population_source_external = initial_population_source_external
        self.build_grid_scenarios = build_grid_scenarios

        self.initial_population = None
        self.parent_one = None
        self.parent_two = None
        self.parent_location_one = None
        self.parent_location_two = None

    def make_initial_population(self, save_population_to_csv=False, initial_pop_size=5):

        complete_architecture = OrderedDict(
            [
                (
                    "LR",
                    np.arange(
                        self.learning_rate[0],
                        self.learning_rate[1],
                        self.learning_rate[2],
                    ),
                )
            ]
        )

        for i in range(len(self.network_architecture.keys())):
            complete_architecture.update(
                {
                    list(self.network_architecture.keys())[i]: np.arange(
                        self.network_architecture[
                            list(self.network_architecture.keys())[i]
                        ][0],
                        self.network_architecture[
                            list(self.network_architecture.keys())[i]
                        ][1],
                        self.network_architecture[
                            list(self.network_architecture.keys())[i]
                        ][2],
                    )
                }
            )

        self.network_architecture = complete_architecture

        if self.initial_population_source_external:
            self.initial_population = pd.read_csv(
                folder_structure.path_input + "/" + "GeneticAlgorithm_20_hist_40.csv",
                index_col=0,
            )

        else:

            if self.build_grid_scenarios:

                learning_rates = [0.01]
                layer_one = [2, 20, 40]
                layer_two = [2, 10, 20, 40]
                layer_three = [0, 2, 10, 20]
                layer_four = [0, 2, 10, 20]

                dict_help = {}
                for i in range(len(learning_rates)):
                    for j in range(len(layer_one)):
                        for k in range(len(layer_two)):
                            for c in range(len(layer_three)):
                                for f in range(len(layer_four)):
                                    dict_help["{}{}{}{}{}".format(i, j, k, c, f)] = [
                                        learning_rates[i],
                                        layer_one[j],
                                        layer_two[k],
                                        layer_three[c],
                                        layer_four[f],
                                    ]
                self.initial_population = pd.DataFrame(dict_help).transpose()
                self.initial_population.rename(
                    columns={
                        0: "LR",
                        1: "Layer1",
                        2: "Layer2",
                        3: "Layer3",
                        4: "Layer4",
                    },
                    inplace=True,
                )
                self.initial_population["Fitness"] = 0
                self.initial_population["Generation"] = 0
                self.initial_population = self.initial_population[
                    ~(
                        (self.initial_population.Layer3 == 0)
                        & (self.initial_population.Layer4 > 0)
                    )
                ].reset_index(drop=True)

                print("Population Size: {}".format(self.initial_population.shape))

                for i in range(self.initial_population.shape[0]):
                    print("Progress: {}".format(i / self.initial_population.shape[0]))
                    training_model = TrainLSTM(
                        training_set=self.training_set_ga,
                        testing_set=self.testing_set_ga,
                        activation=tf.nn.elu,
                        epochs=50,
                        learning_rate=self.initial_population.LR[i],
                        layer_one=self.initial_population["Layer1"][i],
                        layer_two=self.initial_population["Layer2"][i],
                        layer_three=self.initial_population["Layer3"][i],
                        layer_four=self.initial_population["Layer4"][i],
                    )
                    training_model.make_accuracy_measures()

                    self.initial_population.loc[i, "Fitness"] = training_model.fitness

                    print(
                        "Network Architecture: LR: {}, L1: {}, L2: {}, L3: {}, L4: {}".format(
                            self.initial_population.LR[i],
                            self.initial_population.Layer1[i],
                            self.initial_population.Layer2[i],
                            self.initial_population.Layer3[i],
                            self.initial_population.Layer4[i],
                        ),
                    )
                    tf.keras.backend.clear_session()  # important to clear session!
                    del training_model

                if save_population_to_csv:
                    self.initial_population.to_csv(
                        folder_structure.path_input + "/" + "InitialPopulation_all.csv"
                    )

            else:
                ind = pd.DataFrame(
                    0,
                    index=range(initial_pop_size),
                    columns=np.array(
                        list(self.network_architecture.keys())
                        + ["Fitness", "Generation"]
                    ),
                )

                for i in range(ind.shape[0]):
                    for j in range(len(self.network_architecture.keys())):
                        ind[list(self.network_architecture.keys())[j]].iloc[
                            i
                        ] = random.choice(
                            self.network_architecture[
                                list(self.network_architecture.keys())[j]
                            ]
                        )

                self.initial_population = ind

                for i in range(self.initial_population.shape[0]):
                    print("Progress: {}".format(i / self.initial_population.shape[0]))
                    training_model = TrainLSTM(
                        training_set=self.training_set_ga,
                        testing_set=self.testing_set_ga,
                        activation=tf.nn.elu,
                        epochs=7,
                        learning_rate=self.initial_population.LR[i],
                        layer_one=self.initial_population["Layer1"][i],
                        layer_two=self.initial_population["Layer2"][i],
                        layer_three=self.initial_population["Layer3"][i],
                        layer_four=self.initial_population["Layer4"][i],
                    )
                    training_model.make_accuracy_measures()

                    self.initial_population.loc[i, "Fitness"] = training_model.fitness

                    tf.keras.backend.clear_session()  # important to clear session!
                    del training_model

                if save_population_to_csv:
                    self.initial_population.to_csv(
                        folder_structure.path_input
                        + "/"
                        + "InitialPopulation_future_20.csv"
                    )

    def select_parents(self):
        if self.initial_population is None:
            self.make_initial_population()

        df_help = self.initial_population.copy()

        parent1_location = (
            df_help.Fitness[
                np.random.choice(
                    df_help.index, int(df_help.shape[0] * 0.05), replace=False,
                )
            ]
            .nlargest(1)
            .index
        )

        parent2_location = (
            df_help.Fitness[
                np.random.choice(
                    df_help.index, int(df_help.shape[0] * 0.05), replace=False,
                )
            ]
            .nlargest(1)
            .index
        )

        self.parent_location_one = parent1_location
        self.parent_location_two = parent2_location

        self.parent_one = df_help.iloc[parent1_location]
        self.parent_two = df_help.iloc[parent2_location]

    def make_offsprings(self):
        self.select_parents()

        df_test_parent_one = self.parent_one
        df_test_parent_two = self.parent_two
        df_test_parent_one = df_test_parent_one.reset_index(drop=True).reset_index(
            level=0
        )
        df_test_parent_two = df_test_parent_two.reset_index(drop=True).reset_index(
            level=0
        )

        child_one = df_test_parent_one[list(df_test_parent_one.columns[:2])].merge(
            df_test_parent_two[list(df_test_parent_one.columns[2:6])],
            on=df_test_parent_one.index,
        )
        child_two = df_test_parent_two[list(df_test_parent_one.columns[:2])].merge(
            df_test_parent_one[list(df_test_parent_one.columns[2:6])],
            on=df_test_parent_one.index,
        )

        child_one = child_one.drop(["key_0", "index"], axis=1)
        child_two = child_two.drop(["key_0", "index"], axis=1)

        _random_pick = random.choice(child_one.columns)
        _random_pick_2 = random.choice(child_one.columns)
        child_three = child_one.copy()
        child_three[_random_pick] = random.choice(
            self.network_architecture[_random_pick]
        )
        child_three[_random_pick_2] = random.choice(
            self.network_architecture[_random_pick_2]
        )

        _random_pick = random.choice(child_two.columns)
        child_four = child_two.copy()
        child_four[_random_pick] = random.choice(
            self.network_architecture[_random_pick]
        )

        self.initial_population = self.initial_population.append(child_one, sort=False)
        self.initial_population = self.initial_population.append(child_two, sort=False)
        self.initial_population = self.initial_population.append(
            child_three, sort=False
        )
        self.initial_population = self.initial_population.append(child_four, sort=False)

        self.initial_population.reset_index(drop=True, inplace=True)

        individuals_help = self.initial_population.copy()
        individuals_help = individuals_help[individuals_help.Fitness.isna()]

        for i in individuals_help.index:
            train_m = TrainLSTM(
                training_set=self.training_set_ga,
                testing_set=self.testing_set_ga,
                epochs=10,
                learning_rate=individuals_help.LR[i],
                layer_one=individuals_help.Layer1[i],
                layer_two=individuals_help.Layer2[i],
                layer_three=individuals_help.Layer3[i],
                layer_four=individuals_help.Layer4[i],
            )
            train_m.make_accuracy_measures()
            self.initial_population.loc[i, "Fitness"] = train_m.fitness

            tf.keras.backend.clear_session()  # important to clear session!
            del train_m

    def run_complete_genetic_algorithm(
        self, initial_population_size=50, number_of_generations=20
    ):
        if self.initial_population is None:
            self.make_initial_population(
                save_population_to_csv=True, initial_pop_size=initial_population_size
            )

        for iteration in range(number_of_generations):
            print("Progress Generation: {}".format(iteration / number_of_generations))
            print(iteration)
            print(self.parent_location_one, self.parent_location_two)
            self.make_offsprings()


def make_genetic_algorithm_plot(save_plot: bool = False):
    direc_links = [
        "InitialPopulation_all_scenarios_future_1_newfitness.csv",
        "InitialPopulation_all_scenarios_future_5_newfitness.csv",
        "InitialPopulation_all_scenarios_future_20_newfitness.csv",
    ]

    direc_links_2 = [
        "InitialPopulation_sv_1_newfitness.csv",
        "InitialPopulation_sv_5_newfitness.csv",
        "InitialPopulation_sv_20_newfitness.csv",
    ]
    titles_set = [
        "One Day",
        "One Week",
        "One Month",
    ]

    plt.close()
    fig = plt.figure()
    fig.suptitle("Hyperparameter Optimization using Genetic Algorithm", fontsize=16)
    for i in range(3):
        initial_population_scenarios = pd.read_csv(
            folder_structure.path_input + "/" + direc_links[i], index_col=0,
        )
        initial_population_scenarios = initial_population_scenarios.reset_index(level=0)

        df_1 = pd.read_csv(
            folder_structure.path_input + "/" + direc_links_2[i], index_col=0,
        )
        df_2 = df_1.iloc[df_1.Fitness.nlargest(5).index]

        # print PCA
        pca = PCA(n_components=3)
        pca.fit(
            initial_population_scenarios[["LR", "Layer1", "Layer2", "Layer3", "Layer4"]]
        )
        x = pd.DataFrame(
            pca.transform(
                initial_population_scenarios[
                    ["LR", "Layer1", "Layer2", "Layer3", "Layer4"]
                ]
            ),
            columns={"one", "two", "three"},
        ).reset_index(level=0)
        x = x.merge(initial_population_scenarios[["Fitness", "index"]], on="index")

        pca_2 = PCA(n_components=3)
        pca_2.fit(df_1[["LR", "Layer1", "Layer2", "Layer3", "Layer4"]])

        x_2 = pd.DataFrame(
            pca.transform(df_1[["LR", "Layer1", "Layer2", "Layer3", "Layer4"]]),
            columns={"one", "two", "three"},
        ).reset_index(level=0)

        x_2 = x_2.merge(
            df_1.reset_index(drop=True).reset_index(level=0)[["Fitness", "index"]],
            on="index",
        )

        pca_3 = PCA(n_components=3)
        pca_3.fit(df_1[["LR", "Layer1", "Layer2", "Layer3", "Layer4"]])

        x_3 = pd.DataFrame(
            pca.transform(df_2[["LR", "Layer1", "Layer2", "Layer3", "Layer4"]]),
            columns={"one", "two", "three"},
        ).reset_index(level=0)

        x_3 = x_3.merge(
            df_2.reset_index(drop=True).reset_index(level=0)[["Fitness", "index"]],
            on="index",
        )

        from mpl_toolkits.mplot3d import Axes3D

        axs = fig.add_subplot(1, 3, i + 1, projection="3d")
        axs.scatter(
            x_3.one, x_3.two, x_3.three, c="darkred", s=200, alpha=0.5,
        )
        axs.scatter(
            x.one, x.two, x.three, alpha=0.2, marker="o", s=100, c="mediumseagreen"
        )
        axs.scatter(
            x_2.one, x_2.two, x_2.three, c=x_2.Fitness, cmap="binary", alpha=1,
        )
        axs.view_init(elev=12, azim=135)

        axs.set_title(titles_set[i])

    if save_plot:
        os.chdir(folder_structure.output_Graphs)
        fig.savefig("Genetic_Algorithm_Output.png")


# make_genetic_algorithm_plot(save_plot=True)  # plotting results of Genetic Algorithm
