import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def plot_graph(data, col_name):
    """
    Function to plot a graph

    :param data: pandas.DataFrame, data to be plotted
    :param col_name: str, name of the column
    """
    sns.set(style="whitegrid", color_codes=True)
    sns.set_context("talk")

    fig, ax = plt.subplots()

    # Check if the column is binary (has only two unique values)
    if data[col_name].nunique() == 2:
        sns.countplot(data=data, x=col_name, ax=ax)
    else:
        sns.histplot(data, x=col_name, ax=ax)

    ax.set_title(f"Distribution of {col_name}")
    ax.set_xlabel(col_name)
    ax.set_ylabel("Count")

    plt.tight_layout()
    plt.show()


df = pd.read_excel(r'dataset/undummy_dataset.xlsx')

for col in df.columns:
    plot_graph(df, col)
    print("Graph for " + col)