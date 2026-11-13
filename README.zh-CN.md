# 整数神经元实验室

**项目主导：[kangchenghaokang-dot](https://github.com/kangchenghaokang-dot)。**我发起了相关研究探索，确定研究目标和实际约束，并推动工作转向可公开、可复现的成果。我关注的不只是程序能否运行，还包括怎样提出问题、开展对照和给出可检查的依据。[详细贡献与实现分工](CONTRIBUTIONS.md)记录了我的项目主导工作与AI协作范围。

这个项目回答一个小而明确的问题：神经元没有输入时，能否跳过中间更新，仍然逐位保持脉冲时间、查询值和最终状态？

它是研究复现与验证作品，不声称发明事件驱动仿真，也不是完整SNN、临床模型或新硬件。代码新写、输入为固定种子的合成事件，独立于原TTA工程，运行不需要板子、Vivado、密钥或下载数据。

```sh
python run.py verify
python run.py experiment --output results/demo.json
```

需要 Python 3.10+。完整测试可在 PowerShell 设置 `$env:PYTHONPATH="src"` 后运行 `python -m unittest discover -s tests -v`。

建议阅读顺序：先看[数值合同](docs/contract.md)，手算 `g(g(2))` 与一次指数近似的差异；再比较逐tick与事件实现；最后读[实验边界](docs/experiments.md)。结果文件保留不利于事件算法的情形，不把Python运行时间写成芯片性能。

面谈时应该能自己解释：为什么首tick必须完整处理？为什么query可以只观察但最后要物化？为什么稠密输入可能使事件版本更慢？[练习](docs/learning.md)给出可以亲手完成的延伸。

本项目使用AI协助，见[贡献说明](AI_USAGE.md)。仓库展示可核对的工作，不代替维护者理解代码和对结果负责。
