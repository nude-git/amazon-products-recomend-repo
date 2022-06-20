"""
* 
inpのjsonに存在する商品リストの情報をAmazonから取得
上位商品について、評価数・評価値・口コミ・価格の情報をまとめる

* 観点
  - ある程度評価数のある商品について、評価値の分布・統計値はどのようになっているか
  - 価格はどの程度か
  - 役に立った口コミではどのように評価されているか
"""
import logic
from Util import Util

if __name__ == '__main__':
    logic.run_amzn_prd_rec(
        inp_path           = "data/inp/target_prd_list.json",
        browser            = "chrome",
        browser_driver_path= "/usr/local/bin/chromedriver",
        bkup_dir           = f"./data/out/{Util.get_exe_dt_str()}/"
    )
