# LiDO integration for inwerkingtredingsinformatie

[`inwerkingtredingsbepalingen.py`](/parlhistnl/utils/inwerkingtredingsbepalingen.py) contains an integration with the LiDO API provided by KOOP in the `find_inwerkingtredingskb_via_lido` function.

## Authenticating with LiDO
In order to use this integration, you must first request an account from KOOP, because the endpoint that is used is only available for authenticated users. Once you have an account and you want to use this integration, please set the environment variables `PARLHIST_LIDO_USER` and `PARLHIST_LIDO_PASSWORD` accordingly.