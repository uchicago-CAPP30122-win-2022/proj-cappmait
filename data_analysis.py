import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def find_top3_products(df):
    '''
    Create a data structure of top 3 product categories.

    Inputs:
        df(Pandas Dataframe) : Product details in the selected country.

    Outputs:
        products(Pandas Dataframe): A data of top3 product categories in 2019
    '''
    products = df[df["ProductCode"] != "TO"]
    products = products.groupby(["Product","Year"]).sum()\
                     .sort_values(by="Value", ascending=False).reset_index()
    selected_products = products[products["Year"]=="2019"]\
                        .nlargest(3, "Value")["Product"]

    products = products[products["Product"].isin(selected_products)]

    return products
    
def structure_node_link(df, country):
    '''
    Create two data structure(node and link) to plot sankey diagram.

    Inputs:
        df(Pandas Dataframe) : Partners data for the selected country.
        country(str) : Country code

    Returns:
        node_df, link_df
    '''

    partners_ex = df[df["from_code"] == country]
    partners_im = df[df["to_code"] == country]

    node_2019 = list()
    node_2020 = list()

    link_df_2019_ex = find_partners(partners_ex, True, True, node_2019)
    node_2019.append(u'\u2190 Export \u2192')
    link_df_2019_im = find_partners(partners_im, False, True, node_2019)
    node_2019.append('\u2192 Import \u2190')
    importer_index = len(node_2019) - 1
    link_df_2019_im['Target'] = importer_index

    link_df_2020_ex = find_partners(partners_ex, True, False, node_2020, importer_index)
    link_df_2020_im = find_partners(partners_im, False, False, node_2020, importer_index)

    node_df = node_2019 + node_2020
    frames = [link_df_2019_ex, link_df_2019_im, link_df_2020_ex, link_df_2020_im]
    link_df = pd.concat(frames)

    return node_df, link_df


def find_partners(df, is_exporter, is_2019, node, importer_index = 0):
    '''
    Update node list and return link df. 

    Inputs:
        df(Pandas Dataframe) : Partners data for the selected country.
        is_exporter(boolean) : True if the selected country is exporter and False otherwise.
        is_2019(boolean) : True if 2019 and False if 2020.
        node(list) : A list of node labels
        importer_index : The index of importer in node. 0 is the default value when unknown. 

    Outputs:
        link(Pandas Dataframe) : A data of partners link. 
    '''
    link = pd.DataFrame(columns = ['Source','Target','Value','LinkColor'])

    dff = df.sort_values("2019" if is_2019 else "2020", ascending = False).head(10)
    for before, after, exporter, _, importer, _ in dff.itertuples(index=False):
        col = 'lightblue' if is_exporter else 'pink'
        lab = importer if is_exporter else exporter
        middle = 10 if is_exporter else importer_index

        if is_exporter or lab not in node:
            node.append(lab)

        source = node.index(lab)
        
        if is_2019:
            link = link.append({'Source':source, 'Target':middle, 'Value': before, 'LinkColor':col},ignore_index=True)
        else:
            source = source + importer_index + 1
            link = link.append({'Source':middle, 'Target':source, 'Value': after, 'LinkColor':col},ignore_index=True)

    return link

