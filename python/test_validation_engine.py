import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
from esg_data_quality_engine import build_outputs
r,exc,cq,cm=build_outputs()
assert r.Missing_Value_Flag.sum()>0
assert r.Duplicate_Flag.sum()>0
assert r.Invalid_Unit_Flag.sum()>0
assert r.Negative_Emissions_Flag.sum()>0
assert r.Missing_Scope_Flag.sum()>0
assert r.Missing_Source_Flag.sum()>0
assert (r[r.Exception_Count==0].Validation_Status=="Valid").all()
assert len(r)==223
assert len(exc)==int(r.Exception_Count.sum())
assert len(cm)==12*2*12
assert set(cm.Availability.unique())=={"Available","Missing"}
assert cq.Data_Quality_Score.between(0,100).all()
assert (cq.Total_Records>0).all()
summary=pd.read_csv(Path(__file__).resolve().parents[1]/"data"/"esg_quality_summary.csv").iloc[0]
readiness=pd.read_csv(Path(__file__).resolve().parents[1]/"data"/"tableau_readiness.csv")
assert summary.Total_Records==223
assert summary.Exception_Count==len(exc)==37
assert round(summary.Data_Quality_Score,1)==88.4
assert readiness.Readiness_Score.between(0,100).all()
assert set(readiness.Availability.unique())=={"Available","Missing"}
print("All validation engine tests passed.")
