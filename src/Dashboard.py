import numpy as np
from AmazonClient import ProductInfo


class ProductInfoProcessing():
    """
    1.
    2. レコメンド商品について参考情報の作成
       |- レビュー評価の分布
       |- 参考になったレビューのキーワード
    """

    def __init__(self) -> None:
        pass


    def del_none_from_list(self, li:list) -> list:
        return list(filter(lambda x:x is not None, li))


    def calc_mean_std_for_list(self, li:list[float]) -> [float,float]:
        li = self.del_none_from_list(li)
        mean = np.mean(li)
        std  = np.std( li)
        return mean, std


    def calc_products_eval(self, prd_info:dict[int,ProductInfo]) -> dict[int,ProductInfo]:

        mean_review_avg, std_review_avg = self.calc_mean_std_for_list([prd.review_avg for prd in prd_info.values()])
        mean_review_num, std_review_num = self.calc_mean_std_for_list([prd.review_num for prd in prd_info.values()])

        for key, prd in prd_info.items():
            prd_info[key].review_avg_dev = prd.calc_dev_val(prd.review_avg, mean_review_avg, std_review_avg)
            prd_info[key].review_num_dev = prd.calc_dev_val(prd.review_num, mean_review_num, std_review_num)

        return prd_info


    def extract_ranked_products(self, prd_info:dict[int, ProductInfo], num_extract:int) -> dict[int, ProductInfo]:
        """
        :param prd_info:
        :param num_extract:
        :return: {Rank: ProductInfo}
        """
        prd_info = self.calc_products_eval(prd_info)

        prd_key_eval = {key:prd.calc_prd_eval() for key,prd in prd_info.items()}
        prd_key_eval_sorted = sorted(prd_key_eval.items(), reverse=True, key=lambda x:x[1]) # valueでソート

        rank_prd_map = {}
        for rank, (prd_key, eval) in enumerate(prd_key_eval_sorted, start=1):

            rank_prd_map[rank] = prd_info[prd_key]

            if rank >= num_extract:
                break

        return rank_prd_map


    def a(self):
        return


class DisplayDashboard():
    """
    1. 作成した参考情報のWeb上での表示
    """

    def __init__(self, prd_info:ProductInfo) -> None:
        self.prd_info = prd_info

