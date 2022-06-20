import bs4
import numpy  as np
import pandas as pd
import requests
from selenium import webdriver
from time import sleep
from typing import TypeVar, Union
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.select import Select, By
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from typing import Any
from dataclasses import dataclass


@dataclass
class ScrapingParameters():
    # category   : str = ""
    search_word: str = ""
    num_extract: int = 0



@dataclass
class ProductInfo():
    prd_name      : str               = ""
    price         : Union[int,  None] = 0
    review_avg    : Union[float,None] = 0.0
    review_num    : Union[int,  None] = 0
    prd_link      : str               = ""
    review_avg_dev: float             = 0.0
    review_num_dev: float             = 0.0


    def logger(self):
        print()
        print(f">> {self.prd_name}")
        print(f">> 値段:¥{self.price}   評価:{self.review_avg}/5.0   レビュー数:{self.review_num}")


    def calc_dev_val(self, tgt_val:Union[float,None], mean:float, std:float) -> float:
        if tgt_val is None:
            return 0.0
        else:
            return (10.0 * (tgt_val - mean) / std) + 50.0


    def calc_prd_eval(self) -> float:
        # NOTE: 商品の評価点として、レビュー平均点とレビュー数をどの程度重視するか
        w_rev_avg = 3.0
        w_rev_num = 2.0
        return (w_rev_avg*self.review_avg_dev + w_rev_num*self.review_num_dev) / (w_rev_avg + w_rev_num)


@dataclass
class ReviewDetail():
    evaluation: float = 0.0
    title     : str   = ""
    datetime  : str   = "1000/01/01"
    comment   : str   = ""
    num_good  : int   = 0


class AmazonClient():

    def __init__(self, para:ScrapingParameters, browser_type:str, driver_path:str, bkup_dir:str) -> None:
        self.para : ScrapingParameters = para
        self.browser_type      : str = browser_type
        self.driver_path       : str = driver_path
        self.site_url          : str = "https://www.amazon.co.jp/"
        self.bkup_csv_file_path: str = f"{bkup_dir}fetched_data_{para.search_word}.csv"

        # CSS, Tag, ID, Class, etc...
        self.id_dropdown_box    : str = "searchDropdownBox"
        self.css_search_field   : str =  "div.nav-search-field > input"
        self.css_search_button  : str = "div.nav-right > div > span > input"
        self.id_prd_sort_button : str = "s-result-sort-select"
        self.prd_sort_key       : str = "review-rank"
        self.text_to_next_page  : str = "次へ"
        self.css_prd_info       : str = "div.a-section.a-spacing-base"
        self.tag_span_prd_name  : str = "span.a-text-normal"
        self.cls_span_prd_name  : str =  "a-size-base-plus a-color-base a-text-normal" # "a-size-medium a-color-base a-text-normal"
        self.cls_span_prd_price : str = "a-price-whole"
        self.cls_span_review_ave: str = "a-icon-alt"
        self.css_num_of_review  : str = "div.a-row.a-size-small > span:nth-of-type(2) > a > span"
        self.css_prd_link       : str = ".a-size-mini.a-spacing-none.a-color-base.s-line-clamp-2 > .a-link-normal.s-underline-text.s-underline-link-text.s-link-style.a-text-normal"
        self.text_to_all_review : str = "すべてのレビューを参照します"


    def select_driver_type(self) -> Any:

        if self.browser_type == "firefox":
            self.options = webdriver.FirefoxOptions()
            self.options.add_argument("--headless")
            driver = webdriver.Firefox(
                executable_path = self.driver_path,
                options         = self.options
            )

        elif self.browser_type == "chrome":
            self.options = webdriver.ChromeOptions()
            # self.options.add_argument("--headless")
            driver = webdriver.Chrome(
                service = Service(self.driver_path),
                options = self.options
            )

        return driver


    def init_driver(self, init_url:str) -> webdriver:
        driver = self.select_driver_type()
        driver.get(init_url)
        driver.implicitly_wait(5)
        return driver


    def select_product_category(self, driver:webdriver, para:ScrapingParameters) -> None:
        if para.category != "":
            driver.find_element_by_id(self.id_dropdown_box).click()
            select_category = Select(driver.find_element_by_id(self.id_dropdown_box))
            select_category.select_by_value(para.category)


    def search_target_product(self, driver:webdriver, para:ScrapingParameters) -> None:
        driver.find_element(by=By.CSS_SELECTOR, value=self.css_search_field).send_keys(para.search_word)
        driver.find_element(by=By.CSS_SELECTOR, value=self.css_search_button).click()


    def sort_products(self, driver:webdriver, sort_key:str) -> None:
        sort_select = Select(driver.find_element_by_id(self.id_prd_sort_button))
        sort_select.select_by_value(sort_key)


    # TODO: レビューのスクレイピングの方で、次のページへ遷移後、さらに次のページが取れてなさそう。商品の方はいけてるが。。
    def transition_to_next_page(self, driver:webdriver, page_links:list) -> list[str]:
        link_to_next = driver.find_element_by_partial_link_text(self.text_to_next_page) # "次へ"というテキストを持つ要素を取得
        url_to_next = link_to_next.get_attribute("href")                                # リンクを取得
        page_links.append(url_to_next)                                                  # リンクを追加
        link_to_next.click()                                                            # リンク先へ遷移
        sleep(1)
        return page_links


    def transition_to_target_link(self, driver:webdriver, tgt_link_txt:str) -> webdriver:
        tgt_link = driver.find_element_by_link_text(tgt_link_txt)
        tgt_link.click() # リンク先へ遷移
        return driver


    def fetch_target_page_html(self, driver:webdriver, page_link:str) -> bs4.element.ResultSet:
        sleep(1)
        driver.get(page_link)
        source = driver.page_source.encode("utf-8")
        soup = BeautifulSoup(source, "lxml")
        product_soup = soup.select(self.css_prd_info)
        return product_soup


    def collect_links_while_transitioning_to_next(self, driver:webdriver) -> list[str]:
        page_links = [driver.current_url]

        while True:
            try:
                page_links = self.transition_to_next_page(driver, page_links)
            except NoSuchElementException:
                break

        return page_links


    def get_all_product_info(self, driver:webdriver, page_links:list[str]) -> dict[int,ProductInfo]:
        prd_info = {}

        for i, page_link in enumerate(page_links):
            product_soup = self.fetch_target_page_html(driver, page_link)

            for one_prd_info in product_soup:

                if one_prd_info.select_one(self.tag_span_prd_name) is None:
                    continue

                prd_info[i] = self.get_product_info(one_prd_info)

        return prd_info


    def get_prd_name(self, one_prd_info:bs4.element.Tag) -> str:
        try:
            return one_prd_info.find("span", class_=self.cls_span_prd_name).text
        except AttributeError:
            return ""


    def get_prd_price(self, one_prd_info:bs4.element.Tag) -> int:
        try:
            tmp_price = one_prd_info.find("span", class_=self.cls_span_prd_price)
            price = int(tmp_price.text.replace("￥", "").replace(",", "")) if tmp_price else None
            return price
        except AttributeError:
            return 0


    def get_prd_review_average(self, one_prd_info:bs4.element.Tag) -> float:
        try:
            tmp_review_avg = one_prd_info.find("span", class_=self.cls_span_review_ave)
            review_avg = float(tmp_review_avg.text.replace("5つ星のうち", "")) if tmp_review_avg else None
            return review_avg
        except AttributeError:
            return 0.0


    def get_prd_num_of_review(self, one_prd_info:bs4.element.Tag) -> int:
        try:
            tmp_review_num = one_prd_info.select_one(self.css_num_of_review)
            review_num = int(tmp_review_num.text.replace(",", "")) if tmp_review_num else None
            return review_num
        except AttributeError:
            return 0


    def get_prd_link(self, one_prd_info:bs4.element.Tag) -> str:
        try:
            tgt_tag  = one_prd_info.select_one(self.css_prd_link)
            tgt_link = tgt_tag.get("href")
            return f"{self.site_url}{tgt_link}"
        except AttributeError:
            return ""


    def get_product_info(self, one_prd_info:bs4.element.Tag) -> ProductInfo:
        # NOTE: この段階ではまだ偏差得点は計算しない
        product_info = ProductInfo(
            prd_name   = self.get_prd_name(          one_prd_info), # 商品名を取得
            price      = self.get_prd_price(         one_prd_info), # 価格を取得 (値が無い場合 -> None)
            review_avg = self.get_prd_review_average(one_prd_info), # レビューの平均を取得 (値が無い場合 -> None)
            review_num = self.get_prd_num_of_review( one_prd_info), # レビュー数を取得 (値が無い場合 -> None)
            prd_link   = self.get_prd_link(          one_prd_info), # 商品のリンクを取得
        )
        product_info.logger()
        return product_info


    def write_csv(self, prd_info:list[ProductInfo], out_path:str) -> None:
        df_result = pd.DataFrame(prd_info)
        df_result.to_csv(out_path, encoding="utf-8-sig")


    def fetch_products_info(self) -> dict[int,ProductInfo]:

        driver = self.init_driver(self.site_url)

        # self.select_product_category(driver, para)               # 商品カテゴリを選択
        self.search_target_product(  driver, self.para)            # 検索
        self.sort_products(          driver, self.prd_sort_key)    # レビュー評価順にソート

        page_links = self.collect_links_while_transitioning_to_next(driver) # ページを辿りながらリンクを取得していく
        prd_info   = self.get_all_product_info(driver, page_links) # 商品情報をリストに追加していく
        driver.quit()

        # for only backup
        self.write_csv([val for val in prd_info.values()], self.bkup_csv_file_path)

        return prd_info


    def get_all_review_detail(self, driver:webdriver, review_page_links) -> dict:
        return {}


    def fetch_ranked_products_review(self, ranked_prd_info:dict[int,ProductInfo]) -> dict[int:dict[int:ReviewDetail]]:

        all_prd_review_detail = {}

        for prd_key, prd in ranked_prd_info.items():
            driver = self.init_driver(prd.prd_link)
            driver = self.transition_to_target_link(driver, self.text_to_all_review)

            review_page_links  = self.collect_links_while_transitioning_to_next(driver) # ページを辿りながらリンクを取得していく
            review_detail_dict = self.get_all_review_detail(driver, review_page_links)  # レビュー情報をリストに追加していく

            print()
            print(f">> {prd}")
            print(f">> {review_page_links}")

            all_prd_review_detail[prd_key] = review_detail_dict
            driver.quit()

        print()
        print("OK..............")
        exit()

        return

