# For testing inside the Datacube Platform!
%matplotlib inline
%load_ext autoreload
%autoreload 2
import datacube
import numpy as np
import sys
import xarray as xr
import matplotlib.pyplot as plt
from datacube.utils.masking import make_mask, mask_invalid_data, describe_variable_flags
from datacube.utils.rio import configure_s3_access
from dask.distributed import Client

sys.path.append('../')
from phenoxr.phenoXr import Pheno

# client = Client()
# configure_s3_access(aws_unsigned=False, requester_pays=True, client=client)
configure_s3_access(aws_unsigned=False, requester_pays=True)

dc = datacube.Datacube(app="Pheno_test")
dc.list_products().name

veg_proxy = 'NDVI'
dates = ('2019-01-01', '2020-12-31')
inProduct = 'landsat8_c2l2_sr'
resolution = 30
central_lat, central_lon = -35.979288, -72.598012
# central_lat, central_lon = -35.979288, -72.598012
buffer = 0.01
study_area_lat = (central_lat - buffer, central_lat + buffer)
study_area_lon = (central_lon - buffer, central_lon + buffer)
study_area_lat = (-32.4390, -32.0198)
study_area_lon = (-71.3856, -70.4451)

query = {
    "x": study_area_lon,
    "y": study_area_lat,
    "time": dates,
    "output_crs": "EPSG:32719",
    "resolution": (-resolution, resolution),
    "dask_chunks": {"time": 1},
    "group_by":"solar_day",
    'product': inProduct,
    'skip_broken_datasets': True
}

ds = dc.load(
    **query,
)

# ds.update(ds.assign_coords(doy=ds.time.dt.dayofyear,
#                    year=ds.time.dt.year))

doy=ds.time.dt.dayofyear.values
reflectance_names = ["coastal", "blue", "green", "red", "nir08", "swir16", "swir22"]

mask_cloud = make_mask(ds['qa_pixel'], cloud='not_high_confidence', cloud_shadow='not_high_confidence', nodata=False) # genera máscara de nubes e inválidos (landsat aws)
mask_sat = ds['qa_radsat'] == 0 # pixeles no saturados
dsf = ds[reflectance_names].where(mask_cloud & mask_sat) 
dsf.update(dsf.where((dsf >= 1) & (dsf <= 65455), np.nan))
dsf.update(dsf * 0.0000275 + -0.2)

ndvi = ((dsf.nir08 - dsf.red) / (dsf.nir08 + dsf.red)).persist()

# PhenoShape
ans = ndvi.pheno.PhenoShape()
ans_rmse = ans.pheno.RMSE(ndvi).persist()

ans_rmse.plot(robust=True, figsize=(10, 8))

# Pheno LSP
ans2 = ans.pheno.PhenoLSP().persist()

ans_rmse_c = ans.pheno.RMSE(ndvi, LSP_stack=ans2)




if False:
    ## ------- OLD testing, do not run if not necessary ------
    # Get 1 pixel trought time
    onePix = ndvi.sel(x=ndvi.x[1].values, y=ndvi.x[1].values, method="nearest").values

    # 1D application vs time
    onePixr = _getPheno0(y=onePix, doy=doy, interpolType='linear', nan_replace = None, rollWindow=5, nGS = 52)

    # 2D application vs time
    data = _getPheno2(dstack=ndvi.values, doy=doy, 
                      interpolType='linear', nan_replace = None, rollWindow=5, nGS=52)
    ## --------------------------------------------------

    da = xr.DataArray(
        np.sin(0.3 * np.arange(12).reshape(4, 3)),
        [("time", np.arange(4)), ("space", [0.1, 0.2, 0.3])],
        )


    da.sel(time=3)

    da.interp(time=2.5)
    
    
import datacube
from odc.ui import with_ui_cbk
from datacube.utils.rio import configure_s3_access
from dask.distributed import Client

client = Client()
configure_s3_access(aws_unsigned=False, requester_pays=True, client=client)

dc = datacube.Datacube(app="04_Loading_data")
ds = dc.load(product="landsat8_c2l2_sr",
             x=(-71, -70.9),
             y=(-33.3, -33.2),
             time=("2015-01-01", "2022-01-01"),
             output_crs='EPSG:32719',
             resolution=(-30,30),
             progress_cbk=with_ui_cbk(),
             group_by='solar_day',
             dask_chunks={"x": 2048, "y": 2048}
            )

print(ds)
loaded_data = ds.load()  # Este paso no es necesario, a menos que realmente necesites cargar los datos en memoria

# Testing
ds.isel(time=0).red.plot()