from .. import Solver
from ...simulator import Craft, Manager

default_process_round = 8

#本算法根据rika算法魔改,pruning(V2) by zeroneko
def Get_Process_AllowSkills(craft: Craft.Craft, craft_history: list = []) -> set:
    """
    当前可进行的作业技能
    :param craft: 生产配方
    :param craft_history: 历史路线
    :return: 可用技能
    """
    available_actions = set()
    forbidden_actions = set()
    if craft.craft_round == 4:
        available_actions.add("长期俭约")
        available_actions.add("俭约")
    if '俭约' in craft.effects or '坚信' in craft.effects: available_actions.add("坯料制作")
    if '坚信' in craft.effects: forbidden_actions = forbidden_actions.union({"制作", "模范制作", "俭约制作", "精密制作"})
    if '俭约' in craft.effects: forbidden_actions.add("俭约制作")
    available_actions = available_actions.union({"制作", "模范制作", "俭约制作", "精密制作"})
    if '模范制作' in craft_history or '俭约制作' in craft_history:
        forbidden_actions.add("坯料制作")
    if '精密制作' in craft_history:
        forbidden_actions = forbidden_actions.union({"坯料制作", "俭约制作", "模范制作", "制作"})
    if craft.status.name in {"高品质", "最高品质"} or '专心致志' in craft.effects:
        if  (craft.recipe.max_difficulty - craft.current_progress) / craft.craft_data.base_process >= 4:
            available_actions.add('集中制作')
            forbidden_actions = forbidden_actions.union({"模范制作", "俭约制作", "坯料制作"})
        else:
            global default_process_round
            available_actions.add('秘诀')
            available_actions.add('集中加工')
            default_process_round += 1
    result_actions = set()
    for action in available_actions:
        if action not in forbidden_actions and craft.get_skill_availability(action): result_actions.add(action)
    return result_actions

def Get_Quality_AllowSkills(craft: Craft.Craft, craft_history: list = []) -> set:
    """
    当前可进行的加工技能
    :param craft: 生产配方
    :param craft_history: 历史路线
    :return: 可用技能
    """
    available_actions = {"加工", "俭约加工", "坯料加工"}
    forbidden_actions = set()
    inner_quiet = 0 if "内静" not in craft.effects else craft.effects["内静"].param
    if  (craft.recipe.max_quality - craft.current_quality) <= craft.get_skill_quality("比尔格的祝福"): return ({"比尔格的祝福"})
    if '工匠的神技' in craft_history:
        forbidden_actions.add("俭约加工")
    if craft.status.name in {"高品质", "最高品质"}:
        available_actions.add('集中加工')
        available_actions.add('秘诀')
        forbidden_actions = forbidden_actions.union({"加工", "中级加工", "上级加工"})
    else:
        if "改革" not in craft.effects and "阔步" not in craft.effects and (craft.recipe.max_quality-craft.current_quality) <= (2.5 * craft.get_skill_quality("比尔格的祝福")): return {("改革")}
    if "掌握" not in craft.effects and "加工" not in craft.effects and "中级加工" not in craft.effects and inner_quiet < 8: available_actions.add("掌握")
    if "掌握" in craft.effects :
        if craft.effects["掌握"].param < 3 and inner_quiet < 2: forbidden_actions.add("加工")
    if '俭约' in craft.effects:
        available_actions.add("坯料加工")
        forbidden_actions.add("俭约加工")
    else:
        available_actions.add("俭约加工")
        forbidden_actions.add("坯料加工")
    if '加工' in craft.effects:
        available_actions.add("中级加工")
        forbidden_actions = forbidden_actions.union({"加工", "坯料加工", "俭约加工", "改革"})
    if '观察' in craft.effects:
        return ({"注视加工"})
    if '中级加工' in craft.effects:
        available_actions.add("上级加工")
        forbidden_actions = forbidden_actions.union({"加工", "坯料加工", "俭约加工", "改革"})
    if inner_quiet >= 10:
        available_actions.add("工匠的神技")
        available_actions.add("阔步")
    if "阔步" in craft.effects:
        forbidden_actions.add("工匠的神技")
        forbidden_actions.add("阔步")
        if "改革" in craft.effects: available_actions.add("比尔格的祝福")
        if craft.effects["阔步"].param == 1: forbidden_actions.add("改革") #[阔步-X-X-改革]**格式禁用
    if "改革" in craft.effects:
        forbidden_actions.add("掌握")
        forbidden_actions.add("改革")
        if craft.effects["改革"].param % 3: forbidden_actions.add("加工") #[改革-加工-中级加工-上级加工-X]**禁用格式
        if craft.effects["改革"].param % 3 == 1: forbidden_actions.add("阔步") #[改革-X-X-X-阔步],[改革-阔步-X-X]**禁用格式
        if craft.effects["改革"].param >= 3:
            if craft.current_cp < 88: forbidden_actions.add("工匠的神技") #[改革-X-工匠的神技-阔步-比尔格],CP不足
            if craft.current_cp < 81: forbidden_actions.add("俭约加工") #[改革-X-俭约加工-阔步-比尔格],CP不足
        if craft.effects["改革"].param < 3:
            if craft.current_cp < 106: forbidden_actions.add("工匠的神技")#[改革-X-X-工匠的神技-阔步-改革-比尔格]**CP不足
            if craft.current_cp < 95: forbidden_actions.add("俭约加工") #[改革-X-X-俭约加工-X-阔步-改革-比尔格]**CP不足
        if craft.effects["改革"].param // 2 and inner_quiet >= 10: available_actions.add("观察")
    else:
        available_actions.add("改革")
        if inner_quiet >= 2: forbidden_actions = forbidden_actions.union({"加工", "中级加工", "上级加工", "工匠的神技", "俭约加工", "坯料加工", "比尔格的祝福"})
    if craft.current_durability <= 35: forbidden_actions.add("加工")
    if craft.current_durability <= 15: forbidden_actions.add("俭约加工") #耐久不足
    if craft.current_durability <= 20: forbidden_actions = forbidden_actions.union({"观察", "加工", "集中加工", "坯料加工"}) #耐久不足
    if craft.current_durability <= 10: #耐久不足
        forbidden_actions = forbidden_actions.union({"工匠的神技", "阔步", "改革"})
    if craft.current_cp < 56: #[-阔步-比尔格]**CP不足
        forbidden_actions.add("工匠的神技")
        forbidden_actions.add("阔步")
    if craft.current_cp < 42: #[-改革-比尔格]**CP不足
        forbidden_actions.add("改革") 
    if craft.current_cp < 81: #[-俭约加工-阔步-比尔格]**CP不足
        forbidden_actions.add("俭约加工") 
        forbidden_actions.add("观察") 
    if craft.current_cp < 74 and "改革" not in craft.effects and "阔步" not in craft.effects:#[阔步-改革-比尔格]**CP不够
        forbidden_actions.add("阔步")
        forbidden_actions.add("改革")
    result_actions = set()
    for action in available_actions:
        if action not in forbidden_actions and craft.get_skill_availability(action): result_actions.add(action)
    return result_actions

def Generate_Process_Routes(craft: Craft.Craft) -> tuple[Craft.Craft, list]:
    """
    根据进度计算结果
    :param craft(Craft.Craft): _description_
    :return: tuple[Craft.Craft, list]: 最终预估结果, 目标路线图
    """
    queue = [(craft, [])]  
    routes = (craft, [])  
    max_difficulty = craft.recipe.max_difficulty
    base_base_process = craft.craft_data.base_process
    while queue: 
        t_craft, t_history = queue.pop(0)  # 获取一个待办事项
        for action in Get_Process_AllowSkills(t_craft, t_history):
            tt_craft = t_craft.clone()
            tt_craft.use_skill(action)
            tt_craft.status = Manager.mStatus.DEFAULT_STATUS() # 重设球色
            new_data = (tt_craft, t_history + [action])  # 模拟使用技能然后组成一个新的事项
            remaining_prog = (max_difficulty - tt_craft.current_progress) / base_base_process
            if remaining_prog <= 2: # 可以进行加工品质了
                if remaining_prog <= 0.0: continue # 进展条满了
                elif remaining_prog <= 1.2: pass
                elif remaining_prog <= 1.8: tt_craft.current_cp -= 7
                elif remaining_prog <= 2: tt_craft.current_cp -= 12
                tt_craft.current_durability -= 4 # 保留一次制作类技能的耐久
                ttt_craft, ttt_history = Generate_Quality_Routes(tt_craft) # 将当前路径进行品质计算
                if routes[0].current_quality < ttt_craft.current_quality: routes = (ttt_craft, t_history + [action] + ttt_history) # 得到总路径品质最高的解
                elif routes[0].current_quality == ttt_craft.current_quality & routes[0].craft_round >= ttt_craft.craft_round: routes = (ttt_craft, t_history + [action] + ttt_history) # 如果品质相同比较轮次
                continue
            if t_craft.craft_round < default_process_round: queue.insert(0, new_data) # 制作轮次大于默认制作轮次
    return routes[0], routes[1]

def Generate_Quality_Routes(craft: Craft.Craft) -> tuple[Craft.Craft, list]:
    """
    根据品质计算结果
    :param craft: 生产配方
    :return: tuple[Craft.Craft, list]: 最终预估结果, 目标路线图
    """
    queue = [(craft, [])] # 待办事项
    top_route = (craft, []) # 目前最佳项 第一个坑是数据，第二个是技能历史
    if True:
        while queue:
            t_craft, t_history = queue.pop(0)  # 获取一个待办事项
            for action in Get_Quality_AllowSkills(t_craft, t_history):
                tt_craft = t_craft.clone()
                tt_craft.use_skill(action)
                tt_craft.status = Manager.mStatus.DEFAULT_STATUS() # 重设球色
                new_data = (tt_craft, t_history + [action])  # 模拟使用技能然后组成一个新的事项
                if top_route[0].current_quality < tt_craft.current_quality: top_route = new_data # 得到当前路径品质最高的解
                elif top_route[0].current_quality == tt_craft.current_quality and top_route[0].craft_round >= tt_craft.craft_round: top_route = new_data # 如果品质相同比较轮次
                if action == "比尔格的祝福": continue # 比尔格收尾了
                if tt_craft.current_quality == craft.recipe.max_quality: continue #品质满了
                queue.insert(0, new_data) # 将未进行完的事项从重新添加到队列
    return top_route[0], top_route[1]

class Stage1:#作业阶段

    def __init__(self):
        self.queue = []
        self.prev_skill = None

    def is_finished(self, craft: Craft.Craft, prev_skill: str = None) -> bool:
        """
        接口，用于判断本stage是否负责完成
        :param craft: 生产数据
        :param prev_skill: 上一个使用的技能名字
        :return: bool
        """
        remaining_prog = (craft.recipe.max_difficulty - craft.current_progress) / craft.craft_data.base_process
        if remaining_prog > 2: return False
        elif remaining_prog >= 1.8: craft.current_cp -= 12
        elif remaining_prog >= 1.2: craft.current_cp -= 7
        elif remaining_prog > 0: pass
        return True

    def deal(self, craft: Craft.Craft, prev_skill: str = None) -> str:
        if not bool(self.queue) or craft.status.name in {"高品质", "最高品质"}  or prev_skill != self.prev_skill:
            routes, ans = Generate_Process_Routes(craft)
            if ans:
                self.queue = ans
        self.prev_skill = self.queue.pop(0)
        return self.prev_skill

class Stage2:#加工阶段

    def __init__(self):
        self.queue = []
        self.prev_skill = None
    
    def is_finished(self, craft: Craft.Craft, prev_skill: str = None) -> bool:
        """
        接口，用于判断本stage是否负责完成
        :param craft: 生产数据
        :param prev_skill: 上一个使用的技能名字
        :return: bool
        """
        remaining_prog = (craft.recipe.max_difficulty - craft.current_progress) / craft.craft_data.base_process
        if remaining_prog >= 1.8: craft.current_cp -= 12
        elif remaining_prog >= 1.2: craft.current_cp -= 7
        elif remaining_prog > 0: pass
        craft.current_durability -= 4
        if not bool(self.queue) or craft.status.name in {"高品质", "最高品质"}  or prev_skill != self.prev_skill:
            routes, ans = Generate_Quality_Routes(craft)
            if ans:
                self.queue = ans
        return not bool(self.queue)

    def deal(self, craft: Craft.Craft, prev_skill: str = None) -> str:
        """
        接口，返回生产技能
        :param craft: 生产数据
        :param prev_skill: 上一个使用的技能名字
        :return: 生产技能
        """
        self.prev_skill = self.queue.pop(0)
        return self.prev_skill

class Stage3:
        
    def is_finished(self, craft: Craft.Craft, prev_skill: str = None) -> bool:
        """
        接口，用于判断本stage是否负责完成
        :param craft: 生产数据
        :param prev_skill: 上一个使用的技能名字
        :return: bool
        """
        return False

    def deal(self, craft: Craft.Craft, prev_skill: str = None) -> str:
        """
        接口，返回生产技能
        :param craft: 生产数据
        :param prev_skill: 上一个使用的技能名字
        :return: 生产技能
        """
        if prev_skill == "观察": return "注视制作"
        remaining_prog = (craft.recipe.max_difficulty - craft.current_progress) / craft.craft_data.base_process
        if remaining_prog >= 1.8: return "观察"
        elif remaining_prog >= 1.2: return "模范制作"
        else: return "制作"

class RikaSolver(Solver):

    @staticmethod
    def suitable(craft):
        return craft.recipe.recipe_row["RecipeLevelTable"]["ClassJobLevel"] == craft.player.level >= 90 and craft.recipe.status_flag == 0b1111

    def __init__(self, craft, logger):
        super().__init__(craft, logger)
        self.stage = 0
        self.choose_stages = [Stage1, Stage2, Stage3]
        self.process_stages = [s() for s in self.choose_stages]
        self.can_hq = craft.recipe.recipe_row["CanHq"]

    def process(self, craft, used_skill = None) -> str:
        """
        接口，返回生产技能
        :param craft: 生产数据
        :param used_skill: 上一个使用的技能名字
        :return: 推荐技能名称
        """
        if self.stage < 0: return ''
        if craft.craft_round == 1: return '坚信'
        if craft.craft_round == 2: return '掌握'
        if craft.craft_round == 3: return '崇敬'
        while self.process_stages[self.stage].is_finished(craft):
            self.stage += 1
            if self.stage >= len(self.process_stages):
                self.stage = -1
                return ''
        ans = self.process_stages[self.stage].deal(craft, used_skill)
        return ans