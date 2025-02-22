import pandas as pd
import pytest

from pandera import errors
from pandera import (
    Column, DataFrameSchema, Float, Int, String, Hypothesis)
from scipy import stats


def test_dataframe_hypothesis_checks():

    df = pd.DataFrame({
        "col1": range(100, 201),
        "col2": range(0, 101),
    })

    hypothesis_check_schema = DataFrameSchema(
        columns={
            "col1": Column(Int),
            "col2": Column(Int),
        },
        checks=[
            # two-sample test
            Hypothesis(
                test=stats.ttest_ind,
                samples=["col1", "col2"],
                relationship=lambda stat, pvalue, alpha=0.01: (
                    stat > 0 and pvalue / 2 < alpha
                ),
                relationship_kwargs={"alpha": 0.5},
            ),
            # one-sample test
            Hypothesis(
                test=stats.ttest_1samp,
                samples=["col1"],
                relationship=lambda stat, pvalue, alpha=0.01: (
                    stat > 0 and pvalue / 2 < alpha
                ),
                test_kwargs={"popmean": 50},
                relationship_kwargs={"alpha": 0.01},
            ),
        ]
    )

    hypothesis_check_schema.validate(df)

    # raise error when using groupby
    hypothesis_check_schema_groupby = DataFrameSchema(
        columns={
            "col1": Column(Int),
            "col2": Column(Int),
        },
        checks=[
            # two-sample test
            Hypothesis(
                test=stats.ttest_ind,
                samples=["col1", "col2"],
                groupby="col3",
                relationship=lambda stat, pvalue, alpha=0.01: (
                    stat > 0 and pvalue / 2 < alpha
                ),
                relationship_kwargs={"alpha": 0.5},
            ),
        ]
    )
    with pytest.raises(errors.SchemaDefinitionError):
        hypothesis_check_schema_groupby.validate(df)


def test_hypothesis():
    # Example df for tests:
    df = (
        pd.DataFrame({
            "height_in_feet": [6.5, 7, 6.1, 5.1, 4],
            "sex": ["M", "M", "F", "F", "F"]
        })
    )

    # Initialise the different ways of calling a test:
    schema_pass_ttest_on_alpha_val_1 = DataFrameSchema({
        "height_in_feet": Column(Float, [
            Hypothesis.two_sample_ttest(
                sample1="M",
                sample2="F",
                groupby="sex",
                relationship="greater_than",
                alpha=0.5),
        ]),
        "sex": Column(String)
    })

    schema_pass_ttest_on_alpha_val_2 = DataFrameSchema({
        "height_in_feet": Column(Float, [
            Hypothesis(test=stats.ttest_ind,
                       samples=["M", "F"],
                       groupby="sex",
                       relationship="greater_than",
                       relationship_kwargs={"alpha": 0.5}
                       ),
        ]),
        "sex": Column(String)
    })

    schema_pass_ttest_on_alpha_val_3 = DataFrameSchema({
        "height_in_feet": Column(Float, [
            Hypothesis.two_sample_ttest(
                sample1="M",
                sample2="F",
                groupby="sex",
                relationship="greater_than",
                alpha=0.5),
        ]),
        "sex": Column(String)
    })

    schema_pass_ttest_on_custom_relationship = DataFrameSchema({
        "height_in_feet": Column(Float, [
            Hypothesis(
                test=stats.ttest_ind,
                samples=["M", "F"],
                groupby="sex",
                relationship=lambda stat, pvalue, alpha=0.01: (
                    stat > 0 and pvalue / 2 < alpha
                ),
                relationship_kwargs={"alpha": 0.5}
            )
        ]),
        "sex": Column(String),
    })

    # Check the 3 happy paths are successful:
    schema_pass_ttest_on_alpha_val_1.validate(df)
    schema_pass_ttest_on_alpha_val_2.validate(df)
    schema_pass_ttest_on_alpha_val_3.validate(df)
    schema_pass_ttest_on_custom_relationship.validate(df)

    schema_fail_ttest_on_alpha_val_1 = DataFrameSchema({
        "height_in_feet": Column(Float, [
            Hypothesis.two_sample_ttest(
                sample1="M",
                sample2="F",
                groupby="sex",
                relationship="greater_than",
                alpha=0.05),
        ]),
        "sex": Column(String)
    })

    schema_fail_ttest_on_alpha_val_2 = DataFrameSchema({
        "height_in_feet": Column(Float, [
            Hypothesis(test=stats.ttest_ind,
                       samples=["M", "F"],
                       groupby="sex",
                       relationship="greater_than",
                       relationship_kwargs={"alpha": 0.05}),
        ]),
        "sex": Column(String)
    })

    schema_fail_ttest_on_alpha_val_3 = DataFrameSchema({
        "height_in_feet": Column(Float, [
            Hypothesis.two_sample_ttest(
                sample1="M",
                sample2="F",
                groupby="sex",
                relationship="greater_than",
                alpha=0.05),
        ]),
        "sex": Column(String)
    })

    with pytest.raises(errors.SchemaError):
        schema_fail_ttest_on_alpha_val_1.validate(df)
    with pytest.raises(errors.SchemaError):
        schema_fail_ttest_on_alpha_val_2.validate(df)
    with pytest.raises(errors.SchemaError):
        schema_fail_ttest_on_alpha_val_3.validate(df)


def test_two_sample_ttest_hypothesis_relationships():
    """Check allowable relationships in two-sample ttest."""
    for relationship in Hypothesis._RELATIONSHIPS:
        schema = DataFrameSchema({
            "height_in_feet": Column(Float, [
                Hypothesis.two_sample_ttest(
                    sample1="M",
                    sample2="F",
                    groupby="sex",
                    relationship=relationship,
                    alpha=0.5),
            ]),
            "sex": Column(String)
        })
        assert isinstance(schema, DataFrameSchema)

    for relationship in ["foo", "bar", 1, 2, 3, None]:
        with pytest.raises(errors.SchemaError):
            DataFrameSchema({
                "height_in_feet": Column(Float, [
                    Hypothesis.two_sample_ttest(
                        sample1="M",
                        sample2="F",
                        groupby="sex",
                        relationship=relationship,
                        alpha=0.5),
                ]),
                "sex": Column(String)
            })
