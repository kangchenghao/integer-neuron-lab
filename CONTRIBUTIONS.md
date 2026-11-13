# Project ownership and contributions

## Project owner: kangchenghaokang-dot

I initiated the broader exploration of computing architecture and brain-inspired
computation. I set the research goals and practical constraints, supplied the
surrounding hardware-project context, and kept the work moving through questions,
comparisons and changes of direction. I asked for a RISC-V comparison in the
earlier work and challenged whether proposed architecture combinations had a
defensible contribution beyond existing approaches.

I then made a deliberate scope decision: prioritize small, reproducible public
projects that demonstrate research practice, rather than keep searching only for
a TTA-specific novelty claim. Integer Neuron Lab is one concrete artifact built
under that direction. My direct contribution here is research motivation,
project priorities, lightweight delivery requirements and sustained iteration.
The particular integer contract, jump-table implementation, test matrix and
experiment execution were developed with AI assistance.

The surrounding engineering projects supplied motivation, not source files in
this repository. This project does not claim that I invented event-driven
simulation or personally handwrote every implementation or test.

## Division of work

|Work|Attribution|
|---|---|
|Research motivation and overall direction|kangchenghaokang-dot|
|Scope and resource decisions; move to public, reproducible artifacts|kangchenghaokang-dot|
|Questions and feedback driving the wider exploration|kangchenghaokang-dot|
|Specific numerical contract, implementation and test construction|AI-assisted development directed by the project owner|
|Local experiment execution, artifact checks and documentation assembly|AI-assisted; results are recorded rather than attributed to unaided manual work|
|Portfolio planning and scoped model review|AI-assisted planning and review; advisory, not peer review|

## 项目主导与实际贡献

我发起了计算架构与脑科学计算相关的探索，明确目标和资源约束，提供周边硬件工程背景，并通过持续提问、比较和反馈推进工作。在前期探索中，我要求建立RISC-V对照，也追问过已有架构组合是否真的能构成新的研究贡献。

之后我主动调整目标：不再只纠结于TTA的创新标签，而是优先把手头工作做成别人能运行、检查和继续修改的公开作品。本仓库是这一决定的具体成果之一。我的直接贡献主要是研究动机、项目优先级、轻量可复现的交付要求和持续推进；具体整数合同、代码、测试及本地实验执行采用AI协作。

这些贡献与“独立手写全部代码”“发明了事件驱动算法”不同，本仓库不作后两种主张。[学习任务](docs/learning.md)是后续可以亲手完成的延伸，不冒充已经完成的个人研究成果。[AI_USAGE.md](AI_USAGE.md)补充说明实现协作方式。
