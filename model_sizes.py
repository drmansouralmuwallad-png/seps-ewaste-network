"""Model sizes for the computation report (Section 5.1, Table S22): Stage 1 phases (from
stage1_solve_log.json), one Stage 2 instance, and the joint model. Writes model_sizes.json."""
import json, platform, os
import pulp
import model as M
import run_joint as J
m, Z = M.build()
s2 = dict(n_vars=len(m.variables()), n_int=sum(v.cat == "Integer" for v in m.variables()), n_cons=len(m.constraints))
mj, Zj, Y, Zs = J.joint_build()
jt = dict(n_vars=len(mj.variables()), n_int=sum(v.cat == "Integer" for v in mj.variables()), n_cons=len(mj.constraints))
s1 = json.load(open("stage1_solve_log.json"))
import highspy
cpu = next((l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")), "unknown")
mem = next((int(l.split()[1]) for l in open("/proc/meminfo") if l.startswith("MemTotal")), 0)
out = dict(stage1=s1, stage2=s2, joint=jt,
           software=dict(python=platform.python_version(), pulp=pulp.__version__,
                         highs=highspy.Highs().version(), cbc="2.10.3 (bundled with PuLP)",
                         os=platform.system() + " " + platform.release()),
           hardware=dict(cpu=cpu, logical_cpus=os.cpu_count(), mem_gib=round(mem / 1024 / 1024, 1)))
json.dump(out, open("model_sizes.json", "w"), indent=1)
print(out)
