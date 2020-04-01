# Preprocessing Data for the dashboard
# goal is to get a data frame with all the predictions and the data

from run_AutoRegression_Model import *
from run_HAR_model import results_har
from config import folder_structure
from LSTM import TimeSeriesDataPreparationLSTM


class DashboardDataPrep:
    def __init__(self, df_tt, df_validation):

        self.df_tt = df_tt
        self.df_validation = df_validation

        self.df_ar = None
        self.df_har = None
        self.df_lstm_tt = None
        self.df_lstm_valid = None
        self.df_all = None
        self.df_final = None

    def prepare_ar_data(self):
        periods_list = [1, 5, 20]
        lags_list = [1, 3]
        df_tmp_3 = pd.DataFrame()
        df_ar_ = pd.DataFrame()

        data_input = pd.concat(
            [self.df_tt[["DATE", "RV", "RSV_minus", "RSV_plus"]], self.df_validation],
            sort=True,
        ).reset_index(drop=True)

        for lags in range(2):
            for period in range(3):
                ar_instance = TimeSeriesDataPreparationLSTM(
                    df=data_input,
                    future=periods_list[period],
                    lag=lags_list[lags],
                    standard_scaler=False,
                    min_max_scaler=False,
                    log_transform=False,
                    semi_variance=False,
                    jump_detect=True,
                    period_train=list(
                        [
                            pd.to_datetime("20030910", format="%Y%m%d"),
                            pd.to_datetime("20111231", format="%Y%m%d"),
                        ]
                    ),
                    period_test=list(
                        [
                            pd.to_datetime("20030910", format="%Y%m%d"),
                            pd.to_datetime("20030910", format="%Y%m%d"),
                        ]
                    ),
                )
                ar_instance.prepare_complete_data_set()

                if lags_list[lags] == 3:
                    ar_vars = ["RV", "lag_1", "lag_2"]
                else:
                    ar_vars = ["RV"]

                df_tmp = pd.DataFrame(
                    results_auto_regression[
                        "AR_{}_{}".format(periods_list[period], lags_list[lags],)
                    ].ar_model.predict(ar_instance.training_set[ar_vars]),
                    columns={"A({})".format(lags_list[lags])},
                ).reset_index()
                df_tmp["period"] = periods_list[period]

                df_tmp_2 = pd.DataFrame(
                    ar_instance.training_set.DATE, columns={"DATE"}
                ).reset_index()
                df_tmp_2 = df_tmp_2.merge(df_tmp, on="index")
                df_tmp_2 = df_tmp_2.drop(columns=["index"])

                if period == 0:
                    df_tmp_3 = df_tmp_2
                else:
                    df_tmp_3 = pd.concat([df_tmp_3, df_tmp_2])

            if lags == 0:
                df_ar_ = df_tmp_3
            else:
                df_ar_ = df_ar_.merge(df_tmp_3, on=["period", "DATE"])

        self.df_ar = df_ar_

    @staticmethod
    def make_exponential(series, log_transformed: bool = False):
        if log_transformed:
            return np.exp(series)
        else:
            return series

    def prepare_har_data(self):
        data_input = pd.concat(
            [self.df_tt[["DATE", "RV", "RSV_minus", "RSV_plus"]], self.df_validation],
            sort=True,
        ).reset_index(drop=True)

        future_periods = [1, 5, 20]
        semi_variance_list = [True, False]
        log_trans_list = [True, False]
        df_tmp_3 = pd.DataFrame()
        df_tmp_4 = pd.DataFrame()
        df_har_ = pd.DataFrame()

        for log_trans in range(2):
            for semi_variance in range(2):
                for i in range(3):
                    har_instance = HARModelLogTransformed(
                        df=data_input,
                        future=future_periods[i],
                        lags=[4, 20],
                        feature="RV",
                        semi_variance=semi_variance_list[semi_variance],
                        jump_detect=True,
                        log_transformation=log_trans_list[log_trans],
                        period_train=list(
                            [
                                pd.to_datetime("20030910", format="%Y%m%d"),
                                pd.to_datetime("20111231", format="%Y%m%d"),
                            ]
                        ),
                        period_test=list(
                            [
                                pd.to_datetime("20030910", format="%Y%m%d"),
                                pd.to_datetime("20111231", format="%Y%m%d"),
                            ]
                        ),
                    )
                    har_instance.make_testing_training_set()

                    if semi_variance_list[semi_variance] is True:
                        har_variables = ["RSV_plus", "RSV_minus", "RV_w", "RV_m"]
                        semi_variance_indication = "SV"
                    else:
                        har_variables = ["RV_t", "RV_w", "RV_m"]
                        semi_variance_indication = "RV"

                    if log_trans_list[log_trans] is True:
                        log_trans_indication = ",L"
                    else:
                        log_trans_indication = ""

                    df_tmp = pd.DataFrame(
                        results_har[
                            "har_{}_{}_{}".format(
                                future_periods[i],
                                semi_variance_list[semi_variance],
                                log_trans_list[log_trans],
                            )
                        ].model.predict(har_instance.training_set[har_variables]),
                        columns={
                            "H({}{})".format(
                                semi_variance_indication, log_trans_indication
                            )
                        },
                    ).reset_index()
                    df_tmp["period"] = future_periods[i]

                    df_tmp[
                        "H({}{})".format(semi_variance_indication, log_trans_indication)
                    ] = self.make_exponential(
                        df_tmp[
                            "H({}{})".format(
                                semi_variance_indication, log_trans_indication
                            )
                        ],
                        log_transformed=log_trans_list[log_trans],
                    )

                    df_tmp_2 = pd.DataFrame(
                        har_instance.training_set.DATE, columns={"DATE"}
                    ).reset_index()
                    df_tmp_2 = df_tmp_2.merge(df_tmp, on="index")
                    df_tmp_2 = df_tmp_2.drop(columns=["index"])

                    if i == 0:
                        df_tmp_3 = df_tmp_2
                    else:
                        df_tmp_3 = pd.concat([df_tmp_3, df_tmp_2])

                if semi_variance == 0:
                    df_tmp_4 = df_tmp_3
                else:
                    df_tmp_4 = df_tmp_4.merge(df_tmp_3, on=["period", "DATE"])

            if log_trans == 0:
                df_har_ = df_tmp_4
            else:
                df_har_ = df_har_.merge(df_tmp_4, on=["period", "DATE"])

        self.df_har = df_har_

    @staticmethod
    def load_lstm_models():
        semi_variance_list = [True, False]
        periods_list = [1, 5, 20]
        lags_list = [20, 40]

        lstm_dict = {}

        for semi_variance in range(2):
            for lags in range(2):
                for period in range(3):
                    lstm_dict[
                        "LSTM_{}_{}_{}".format(
                            semi_variance_list[semi_variance],
                            periods_list[period],
                            lags_list[lags],
                        )
                    ] = tf.keras.models.load_model(
                        folder_structure.output_LSTM
                        + "/"
                        + "LSTM_{}_{}_{}.h5".format(
                            semi_variance_list[semi_variance],
                            periods_list[period],
                            lags_list[lags],
                        )
                    )

        return lstm_dict

    def prepare_lstm_data(self):
        semi_variance_list = [True, False]
        periods_list = [1, 5, 20]
        lags_list = [20, 40]
        data_set_list = [self.df_tt, self.df_validation]
        df_tpm_3 = pd.DataFrame()
        df_tmp_4 = pd.DataFrame()
        df_lstm_ = pd.DataFrame()

        lstm_dict = self.load_lstm_models()

        for data_set in range(2):
            for semi_variance in range(2):
                for lags in range(2):
                    for period in range(3):

                        lstm_instance = TimeSeriesDataPreparationLSTM(
                            df=data_set_list[data_set],
                            future=periods_list[period],
                            lag=lags_list[lags],
                            standard_scaler=False,
                            min_max_scaler=True,
                            log_transform=True,
                            semi_variance=semi_variance_list[semi_variance],
                            jump_detect=True,
                            period_train=list(
                                [
                                    pd.to_datetime("20030910", format="%Y%m%d"),
                                    pd.to_datetime("20111231", format="%Y%m%d"),
                                ]
                            ),
                            period_test=list(
                                [
                                    pd.to_datetime("20030910", format="%Y%m%d"),
                                    pd.to_datetime("20111231", format="%Y%m%d"),
                                ]
                            ),
                        )
                        lstm_instance.prepare_complete_data_set()
                        lstm_instance.reshape_input_data()

                        if semi_variance_list[semi_variance] is True:
                            semi_variance_indication = "SV"
                        else:
                            semi_variance_indication = "RV"

                        df_tmp = pd.DataFrame(
                            lstm_instance.back_transformation(
                                lstm_dict[
                                    "LSTM_{}_{}_{}".format(
                                        semi_variance_list[semi_variance],
                                        periods_list[period],
                                        lags_list[lags],
                                    )
                                ].predict(lstm_instance.train_matrix)
                            ),
                            columns={
                                "L({},{})".format(
                                    semi_variance_indication, lags_list[lags]
                                )
                            },
                        ).reset_index()
                        df_tmp["period"] = periods_list[period]

                        df_tmp_2 = pd.DataFrame(
                            lstm_instance.training_set.DATE, columns={"DATE"}
                        ).reset_index()
                        df_tmp_2 = df_tmp_2.merge(df_tmp, on="index")
                        df_tmp_2 = df_tmp_2.drop(columns=["index"])

                        if period == 0:
                            df_tpm_3 = df_tmp_2
                        else:
                            df_tpm_3 = pd.concat([df_tpm_3, df_tmp_2])

                    if lags == 0:
                        df_tmp_4 = df_tpm_3
                    else:
                        df_tmp_4 = df_tmp_4.merge(df_tpm_3, on=["period", "DATE"])

                if semi_variance == 0:
                    df_lstm_ = df_tmp_4
                else:
                    df_lstm_ = df_lstm_.merge(df_tmp_4, on=["period", "DATE"])

            if data_set == 0:
                self.df_lstm_tt = df_lstm_
            else:
                self.df_lstm_valid = df_lstm_

    def prepare_all_data(self):
        if self.df_ar is None:
            self.prepare_ar_data()

        if self.df_har is None:
            self.prepare_har_data()

        if any(df is None for df in [self.df_lstm_tt, self.df_lstm_valid]):
            self.prepare_lstm_data()

    def merge_all(self):
        if any(
            data_frame is None
            for data_frame in [
                self.df_ar,
                self.df_har,
                self.df_lstm_tt,
                self.df_lstm_valid,
            ]
        ):
            self.prepare_all_data()

        df_tmp = self.df_ar.merge(self.df_har, on=["period", "DATE"])
        df_lstm_complete = pd.concat([self.df_lstm_tt, self.df_lstm_valid]).reset_index(
            drop=True
        )

        self.df_final = df_tmp.merge(df_lstm_complete, on=["period", "DATE"])

        # add training, testing, validation indicator
        data_input = pd.concat(
            [self.df_tt[["DATE", "RV", "RSV_minus", "RSV_plus"]], self.df_validation],
            sort=True,
        ).reset_index(drop=True)

        self.df_final["dataset"] = np.NAN
        self.df_final.dataset[
            (self.df_final.DATE >= pd.to_datetime("20030910", format="%Y%m%d"))
            & (self.df_final.DATE <= pd.to_datetime("20091231", format="%Y%m%d"))
        ] = "training"

        self.df_final.dataset[
            (self.df_final.DATE >= pd.to_datetime("20100101", format="%Y%m%d"))
            & (self.df_final.DATE <= pd.to_datetime("20101231", format="%Y%m%d"))
        ] = "testing"

        self.df_final.dataset[
            (self.df_final.DATE >= pd.to_datetime("20110101", format="%Y%m%d"))
            & (self.df_final.DATE <= pd.to_datetime("20111231", format="%Y%m%d"))
        ] = "validation"

        self.df_final = self.df_final.merge(data_input[["DATE", "RV"]], on="DATE")


# # add this shit to a loop
# df_export_2["dataset"] = np.NAN
#
# df_export_2.dataset[
#     (df_export_2.DATE >= pd.to_datetime("20040910", format="%Y%m%d"))
#     & (df_export_2.DATE < pd.to_datetime("20050910", format="%Y%m%d"))
# ] = "training"
#
# df_export_2.dataset[
#     (df_export_2.DATE >= pd.to_datetime("20040910", format="%Y%m%d"))
#     & (df_export_2.DATE < pd.to_datetime("20050910", format="%Y%m%d"))
# ] = "testing"
#
# df_export_2.dataset[
#     (df_export_2.DATE >= pd.to_datetime("20040910", format="%Y%m%d"))
#     & (df_export_2.DATE < pd.to_datetime("20050910", format="%Y%m%d"))
# ] = "validation"
#
# df_export_2 = df_export_2.merge(data_frame_final[["DATE", "RV"]], on="DATE")  # works


df_m = pd.read_csv(
    folder_structure.path_input + "/" + "RealizedMeasures03_10.csv", index_col=0
)
df_m.DATE = df_m.DATE.values
df_m.DATE = pd.to_datetime(df_m.DATE, format="%Y%m%d")

df = pd.read_csv(folder_structure.path_input + "/" + "DataFeatures.csv", index_col=0)
df.DATE = df.DATE.values
df.DATE = pd.to_datetime(df.DATE, format="%Y%m%d")

x = DashboardDataPrep(df_tt=df_m, df_validation=df)
x.merge_all()

x.df_final

x.df_final.to_csv(folder_structure.path_input + "/" + "DashboardData.csv")

#
#
# # add the same for autoregression
# df_m = df_m[["DATE", "RV", "RSV_minus", "RSV_plus"]]
# data_frame_final = pd.concat(
#     [pd.DataFrame(df_m), pd.DataFrame(df)], sort=True
# ).reset_index(drop=True)
#
# periods_list = [1, 5, 20]
# lags_list = [1, 3]
# df_final = pd.DataFrame()
# df_export_2 = pd.DataFrame()
#
#
# for lags in range(2):
#     for period in range(3):
#         lstm_instance = TimeSeriesDataPreparationLSTM(
#             df=df_m,
#             future=periods_list[period],
#             lag=lags_list[lags],
#             standard_scaler=False,
#             min_max_scaler=False,
#             log_transform=False,
#             semi_variance=False,
#             jump_detect=True,
#             period_train=list(
#                 [
#                     pd.to_datetime("20030910", format="%Y%m%d"),
#                     pd.to_datetime("20111231", format="%Y%m%d"),
#                 ]
#             ),
#             period_test=list(
#                 [
#                     pd.to_datetime("20030910", format="%Y%m%d"),
#                     pd.to_datetime("20030910", format="%Y%m%d"),
#                 ]
#             ),
#         )
#         lstm_instance.prepare_complete_data_set()
#
#         if lags_list[lags] == 3:
#             ar_vars = ["RV", "lag_1", "lag_2"]
#         else:
#             ar_vars = ["RV"]
#
#         df_tmp = pd.DataFrame(
#             results_auto_regression[
#                 "AR_{}_{}".format(periods_list[period], lags_list[lags],)
#             ].ar_model.predict(lstm_instance.training_set[ar_vars]),
#             columns={"A({})".format(lags_list[lags])},
#         ).reset_index()
#         df_tmp["period"] = periods_list[period]
#
#         df_x = pd.DataFrame(
#             lstm_instance.training_set.DATE, columns={"DATE"}
#         ).reset_index()
#         df_x = df_x.merge(df_tmp, on="index")
#         df_x = df_x.drop(columns=["index"])
#
#         if period == 0:
#             df_final = df_x
#         else:
#             df_final = pd.concat([df_final, df_x])
#
#     if lags == 0:
#         df_export_2 = df_final
#     else:
#         df_export_2 = df_export_2.merge(df_final, on=["period", "DATE"])
#
#
# # LSTM starts here
# semi_variance_list = [True, False]
# periods_list = [1, 5, 20]
# lags_list = [20, 40]
# df_final = pd.DataFrame()
# df_export = pd.DataFrame()
# df_export_2 = pd.DataFrame()
#
# for semi_variance in range(2):
#     for lags in range(2):
#         for period in range(3):
#             lstm_model = tf.keras.models.load_model(
#                 folder_structure.output_LSTM
#                 + "/"
#                 + "LSTM_{}_{}_{}.h5".format(
#                     semi_variance_list[semi_variance],
#                     periods_list[period],
#                     lags_list[lags],
#                 )
#             )
#
#             lstm_instance = TimeSeriesDataPreparationLSTM(
#                 df=df_m,
#                 future=periods_list[period],
#                 lag=lags_list[lags],
#                 standard_scaler=False,
#                 min_max_scaler=True,
#                 log_transform=True,
#                 semi_variance=semi_variance_list[semi_variance],
#                 jump_detect=True,
#                 period_train=list(
#                     [
#                         pd.to_datetime("20030910", format="%Y%m%d"),
#                         pd.to_datetime("20111231", format="%Y%m%d"),
#                     ]
#                 ),
#                 period_test=list(
#                     [
#                         pd.to_datetime("20030910", format="%Y%m%d"),
#                         pd.to_datetime("20030910", format="%Y%m%d"),
#                     ]
#                 ),
#             )
#             lstm_instance.prepare_complete_data_set()
#             lstm_instance.reshape_input_data()
#
#             if semi_variance_list[semi_variance] is True:
#                 semi_variance_indication = "SV"
#             else:
#                 semi_variance_indication = "RV"
#
#             df_tmp = pd.DataFrame(
#                 lstm_instance.back_transformation(
#                     lstm_model.predict(lstm_instance.train_matrix)
#                 ),
#                 columns={"L({},{})".format(semi_variance_indication, lags_list[lags])},
#             ).reset_index()
#             df_tmp["period"] = periods_list[period]
#
#             df_x = pd.DataFrame(
#                 lstm_instance.training_set.DATE, columns={"DATE"}
#             ).reset_index()
#             df_x = df_x.merge(df_tmp, on="index")
#             df_x = df_x.drop(columns=["index"])
#
#             if period == 0:
#                 df_final = df_x
#             else:
#                 df_final = pd.concat([df_final, df_x])
#
#         if lags == 0:
#             df_export = df_final
#         else:
#             df_export = df_export.merge(df_final, on=["period", "DATE"])
#
#     if semi_variance == 0:
#         df_export_2 = df_export
#     else:
#         df_export_2 = df_export_2.merge(df_export, on=["period", "DATE"])
#
#
# # HAR Model Data Transformation
# df_m = df_m[["DATE", "RV", "RSV_minus", "RSV_plus"]]
# data_frame_final = pd.concat([pd.DataFrame(df_m), pd.DataFrame(df)]).reset_index(
#     drop=True
# )
#
#
# def make_exponential(series, log_transformed: bool = False):
#     if log_transformed:
#         return np.exp(series)
#     else:
#         return series
#
#
# future_periods = [1, 5, 20]
# semi_variance_list = [True, False]
# log_trans_list = [True, False]
# df_final = pd.DataFrame()
# df_export = pd.DataFrame()
# df_export_2 = pd.DataFrame()
#
# for log_trans in range(2):
#     for semi_variance in range(2):
#         for i in range(3):
#             har_instance = HARModelLogTransformed(
#                 df=data_frame_final,
#                 future=future_periods[i],
#                 lags=[4, 20],
#                 feature="RV",
#                 semi_variance=semi_variance_list[semi_variance],
#                 jump_detect=True,
#                 log_transformation=log_trans_list[log_trans],
#                 period_train=list(
#                     [
#                         pd.to_datetime("20030910", format="%Y%m%d"),
#                         pd.to_datetime("20111231", format="%Y%m%d"),
#                     ]
#                 ),
#                 period_test=list(
#                     [
#                         pd.to_datetime("20030910", format="%Y%m%d"),
#                         pd.to_datetime("20030910", format="%Y%m%d"),
#                     ]
#                 ),
#             )
#             har_instance.make_testing_training_set()
#
#             if semi_variance_list[semi_variance] is True:
#                 har_variables = ["RSV_plus", "RSV_minus", "RV_w", "RV_m"]
#                 semi_variance_indication = "SV"
#             else:
#                 har_variables = ["RV_t", "RV_w", "RV_m"]
#                 semi_variance_indication = "RV"
#
#             if log_trans_list[log_trans] is True:
#                 log_trans_indication = ",L"
#             else:
#                 log_trans_indication = ""
#
#             df_tmp = pd.DataFrame(
#                 results_har[
#                     "har_{}_{}_{}".format(
#                         future_periods[i],
#                         semi_variance_list[semi_variance],
#                         log_trans_list[log_trans],
#                     )
#                 ].model.predict(har_instance.training_set[har_variables]),
#                 columns={
#                     "H({}{})".format(semi_variance_indication, log_trans_indication)
#                 },
#             ).reset_index()
#             df_tmp["period"] = future_periods[i]
#
#             df_tmp[
#                 "H({}{})".format(semi_variance_indication, log_trans_indication)
#             ] = make_exponential(
#                 df_tmp[
#                     "H({}{})".format(semi_variance_indication, log_trans_indication)
#                 ],
#                 log_transformed=log_trans_list[log_trans],
#             )
#
#             df_x = pd.DataFrame(
#                 har_instance.training_set.DATE, columns={"DATE"}
#             ).reset_index()
#             df_x = df_x.merge(df_tmp, on="index")
#             df_x = df_x.drop(columns=["index"])
#
#             if i == 0:
#                 df_final = df_x
#             else:
#                 df_final = pd.concat([df_final, df_x])
#
#         if semi_variance == 0:
#             df_export = df_final
#         else:
#             df_export = df_export.merge(df_final, on=["period", "DATE"])
#
#     if log_trans == 0:
#         df_export_2 = df_export
#     else:
#         df_export_2 = df_export_2.merge(df_export, on=["period", "DATE"])
#
#
# # add this shit to a loop
# df_export_2["dataset"] = np.NAN
#
# df_export_2.dataset[
#     (df_export_2.DATE >= pd.to_datetime("20040910", format="%Y%m%d"))
#     & (df_export_2.DATE < pd.to_datetime("20050910", format="%Y%m%d"))
# ] = "training"
#
# df_export_2.dataset[
#     (df_export_2.DATE >= pd.to_datetime("20040910", format="%Y%m%d"))
#     & (df_export_2.DATE < pd.to_datetime("20050910", format="%Y%m%d"))
# ] = "testing"
#
# df_export_2.dataset[
#     (df_export_2.DATE >= pd.to_datetime("20040910", format="%Y%m%d"))
#     & (df_export_2.DATE < pd.to_datetime("20050910", format="%Y%m%d"))
# ] = "validation"
#
# df_export_2 = df_export_2.merge(data_frame_final[["DATE", "RV"]], on="DATE")  # works
