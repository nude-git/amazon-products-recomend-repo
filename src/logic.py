import json
import pathlib
from typing import TypeVar, Union
from AmazonClient import AmazonClient, ScrapingParameters
from Dashboard import ProductInfoProcessing, DisplayDashboard


def run_amzn_prd_rec(inp_path:str, browser:str, browser_driver_path:str, bkup_dir:str) -> None:
    target_prd_list = init(inp_path, bkup_dir)
    for key, target_prd_dict in target_prd_list.items():
        executing_for_1prd(target_prd_dict["search_word"], target_prd_dict["num_extract"], browser, browser_driver_path, bkup_dir)


def init(inp_path:str, bkup_dir:str) -> dict[dict[str,Union[str,int]]]:
    pathlib.Path(bkup_dir).mkdir()
    target_prd_list = json.load(open(inp_path, "r"))
    return target_prd_list


def executing_for_1prd(search_word:str, num_extract:int, browser:str, browser_driver_path:str, bkup_dir:str) -> None:

    para = ScrapingParameters(search_word, num_extract)
    amzn = AmazonClient(para, browser, browser_driver_path, bkup_dir)
    proc = ProductInfoProcessing()
    # dash = DisplayDashboard()

    prd_info               = amzn.fetch_products_info()
    ranked_products_info   = proc.extract_ranked_products(prd_info, num_extract)
    ranked_products_review = amzn.fetch_ranked_products_review(ranked_products_info)
