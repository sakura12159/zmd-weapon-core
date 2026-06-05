import sys
import json
from collections import defaultdict

from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QCheckBox, QHBoxLayout, QVBoxLayout, QButtonGroup, QTabWidget, \
    QWidget, QTextEdit, QFrame, QSizePolicy, QLineEdit, QMessageBox
from PySide6.QtCore import Qt

from utils import get_root_path

class HDividerWidget(QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)

class VDividerWidget(QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFrameShape(QFrame.Shape.VLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)

class WeaponCheckerWidget(QWidget):
    def __init__(self, parent, config):
        super().__init__(parent=parent)
        self.basic_tag = None
        self.extra_tag = None
        self.skill_tag = None

        self.check_inventory = False
        self.inventory = None
        self.config = config
        self.tag_mp = {
            '基础词条': 'basic_tag',
            '附加词条': 'extra_tag',
            '技能词条': 'skill_tag'
        }

        self.init()

    def load_inventory(self):
        if not (get_root_path() / self.config['inventory_path']).exists():
            QMessageBox.critical(self, 'inventory.json 文件不存在', '要使用检查仓储功能，需要在当前路径下放置 inventory.json 文件！')
            return
        
        with open(get_root_path() / self.config['inventory_path'], 'r', encoding='utf-8') as f:
            inventory = json.load(f)
        self.inventory = inventory
    
    def init_tag_layout(self, parent, tag_pool_name, tag_pool, n_col):
        tag_layout = QVBoxLayout()
        tag_layout.addWidget(QLabel(tag_pool_name, parent=parent, alignment=Qt.AlignmentFlag.AlignHCenter))
        tag_layout.addSpacing(10)
        button_group = QButtonGroup(parent)
        button_group.buttonClicked.connect(lambda btn: setattr(self, self.tag_mp[tag_pool_name], btn.text()))

        for i in range(0, len(tag_pool), n_col):
            row_layout = QHBoxLayout()
            for j in range(i, i + n_col):
                if j >= len(tag_pool):  # 空缺的 tag 放一个 widget 占位
                    checkbox = QWidget(parent=parent)
                else:
                    checkbox = QCheckBox(tag_pool[j], parent=parent)
                    button_group.addButton(checkbox)
                row_layout.addWidget(checkbox)
            tag_layout.addLayout(row_layout)
        return tag_layout
    
    def check_weapon_core(self):
        """检查武器基质在当前版本是否有可适配的武器"""
        if self.check_inventory:
            self.load_inventory()

        if self.basic_tag is None or self.extra_tag is None or self.skill_tag is None:
            text = '有未选择的词条项，请在每个词条池中选择一条！'
        else:
            # 武器按标签分组
            weapon_props = self.config['weapon_props']

            weapons_grouped_by_tag = defaultdict(list)
            for weapon in weapon_props:
                weapons_grouped_by_tag[tuple(weapon_props[weapon][1])].append(weapon)

            tags = (self.basic_tag, self.extra_tag, self.skill_tag)
            if tags not in weapons_grouped_by_tag:
                text = f'\n基质 [{self.basic_tag} - {self.extra_tag} - {self.skill_tag}] 没有适配的武器\n'
            else:
                matched_weapons = sorted(weapons_grouped_by_tag[tags], key=lambda x: weapon_props[x][0], reverse=True)
                text = [f'\n基质 [{self.basic_tag} - {self.extra_tag} - {self.skill_tag}] 有适配的武器：\n']
                for weapon in matched_weapons:
                    text.append(f'\t{weapon}({weapon_props[weapon][0]}*)')
                    if self.check_inventory:
                        text[-1] += ' ' * 10 + \
                            f' - 武器{"已" if self.inventory['weapon_possessed'][weapon] else "未"}拥有，基质{"已" if self.inventory['weapon_core_possessed'][weapon] else "未"}拥有'
                text = '\n'.join(text)
        self.text_edit.setText(text) 
    
    def init(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(50, 50, 50, 50)

        layout = self.init_tag_layout(self, '基础词条', self.config['tag_pools']['basic_tag_pool'], self.config['basic_tag_n_col'])
        main_layout.addLayout(layout)
        main_layout.addSpacing(25)
        main_layout.addWidget(HDividerWidget(parent=self))
        main_layout.addSpacing(25)
        layout = self.init_tag_layout(self, '附加词条', self.config['tag_pools']['extra_tag_pool'], self.config['extra_tag_n_col'])
        main_layout.addLayout(layout)
        main_layout.addSpacing(25)
        main_layout.addWidget(HDividerWidget(parent=self))
        main_layout.addSpacing(25)
        layout = self.init_tag_layout(self, '技能词条', self.config['tag_pools']['skill_tag_pool'], self.config['skill_tag_n_col'])
        main_layout.addLayout(layout)
        main_layout.addSpacing(25)
        main_layout.addWidget(HDividerWidget(parent=self))
        main_layout.addSpacing(25)

        hbox = QHBoxLayout()

        vbox = QVBoxLayout()
        check_inventory_checkbox = QCheckBox('检查仓储', parent=self)
        check_inventory_checkbox.clicked.connect(lambda: setattr(self, 'check_inventory', check_inventory_checkbox.isChecked()))  # 更新 check_inventory 属性
        vbox.addWidget(check_inventory_checkbox)
        confirm_button = QPushButton('检查基质', parent=self)
        confirm_button.clicked.connect(self.check_weapon_core)
        confirm_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)  # 占满上下空间
        vbox.addWidget(confirm_button)

        hbox.addLayout(vbox)

        self.text_edit = QTextEdit(parent=self, readOnly=True)
        hbox.addWidget(self.text_edit)
        main_layout.addLayout(hbox)

        self.setLayout(main_layout)

class WeaponCorePlannerWidget(QWidget):
    def __init__(self, parent, config):
        super().__init__(parent=parent)
        self.target_weapons_str = ''
        self.check_inventory = False
        self.inventory = None
        self.config = config

        self.init()

    def load_inventory(self):
        if not (get_root_path() / self.config['inventory_path']).exists():
            QMessageBox.critical(self, 'inventory.json 文件不存在', '要使用检查仓储功能，需要在当前路径下放置 inventory.json 文件！')
            return
        
        with open(get_root_path() / self.config['inventory_path'], 'r', encoding='utf-8') as f:
            inventory = json.load(f)
        self.inventory = inventory

    def plan(self):
        """
        根据希望刷取的武器给出每个副本可以点哪些其他词条来最高效地刷取目标武器与其他武器基质，当有多个目标武器时部分武器可能不在最优计划之内，可按需输入单个目标武器\n
        优先级先后顺序为：\n
            1.目标武器
            2.其他武器\n
        """
        if self.check_inventory:
            self.load_inventory()

        target_weapons = self.target_weapons_str.replace(',', ' ').replace('，', ' ').split()
        if not target_weapons or any(weapon not in self.config['weapon_props'] for weapon in target_weapons):
            text = '输入有误，请检查武器名称并按提示修改输入格式！'
        else:
            text = []
            weapon_props = self.config['weapon_props']
            places = self.config['places']

            if self.check_inventory and self.inventory is not None:
                for weapon in target_weapons:
                    if self.inventory['weapon_core_possessed'][weapon]:
                        text.append(f'武器 [{weapon}] 已有适配基质\n')

            weapons_list = sorted(weapon_props.keys(), key=lambda x: weapon_props[x][0])
            targets = set(target_weapons)
            max_target_weapons = max_nontarget_weapons = 0
            best_weapon_indices_lists, cur_weapon_indices_list = [], []
            tags_vis_list, tags_vis, basic_tag_vis, extra_skill_tag_vis = [], set(), set(), None

            def helper(i):
                nonlocal basic_tag_vis, extra_skill_tag_vis
                if i < 0:
                    nonlocal max_target_weapons, max_nontarget_weapons
                    cur_target_weapons = sum(1 for idx in cur_weapon_indices_list if weapons_list[idx] in targets)
                    cur_nontarget_weapons = len(cur_weapon_indices_list) - cur_target_weapons
                    # 更新最优统计值
                    if cur_target_weapons > max_target_weapons or cur_target_weapons == max_target_weapons and cur_nontarget_weapons > max_nontarget_weapons:
                        best_weapon_indices_lists.clear()
                        tags_vis_list.clear()
                        tags_vis.clear()
                        max_target_weapons, max_nontarget_weapons = cur_target_weapons, cur_nontarget_weapons
                    # 判断当前武器选择是否为最优配置
                    if cur_target_weapons == max_target_weapons and cur_nontarget_weapons == max_nontarget_weapons:
                        cur_tags = (*sorted(basic_tag_vis), extra_skill_tag_vis)
                        if cur_tags not in tags_vis:
                            best_weapon_indices_lists.append(cur_weapon_indices_list.copy())
                            tags_vis.add(cur_tags)
                            tags_vis_list.append(cur_tags)
                    return

                helper(i - 1)

                basic_tag, extra_tag, skill_tag = weapon_props[weapons_list[i]][1]
                if extra_tag not in extra_tag_pool or skill_tag not in skill_tag_pool:  # 这个武器适配的基质不在当前副本的产出范围内
                    return
                if extra_skill_tag_vis is None:  # 没选过任何基质
                    # 选附加词条
                    extra_skill_tag_vis = extra_tag
                    basic_tag_vis.add(basic_tag)
                    cur_weapon_indices_list.append(i)
                    helper(i - 1)
                    cur_weapon_indices_list.pop()
                    extra_skill_tag_vis = None
                    basic_tag_vis.remove(basic_tag)
                    # 选技能词条
                    extra_skill_tag_vis = skill_tag
                    basic_tag_vis.add(basic_tag)
                    cur_weapon_indices_list.append(i)
                    helper(i - 1)
                    cur_weapon_indices_list.pop()
                    extra_skill_tag_vis = None
                    basic_tag_vis.remove(basic_tag)
                else:
                    if extra_tag != extra_skill_tag_vis and skill_tag != extra_skill_tag_vis:  # 这个武器适配的基质词条不能与当前已选择的武器列表兼容
                        return
                    # 附加或三词条兼容
                    if basic_tag in basic_tag_vis:  # 基础词条兼容
                        cur_weapon_indices_list.append(i)
                        helper(i - 1)
                        cur_weapon_indices_list.pop()
                    elif len(basic_tag_vis) < 3:  # 基础条不兼容但仍有选择余地
                        basic_tag_vis.add(basic_tag)
                        cur_weapon_indices_list.append(i)
                        helper(i - 1)
                        cur_weapon_indices_list.pop()
                        basic_tag_vis.remove(basic_tag)

            text.append('\n开始计算每个副本的刷取目标武器基质的最佳词条搭配\n')
            for place, place_tag_pool in places.items():
                _, extra_tag_pool, skill_tag_pool = place_tag_pool
                helper(len(weapons_list) - 1)

                if max_target_weapons > 0:
                    text.append(f'副本 [{place}] 最多可获得 [{max_target_weapons}] 个目标武器基质与 [{max_nontarget_weapons}] 个其他武器基质\n')
                    for idx, (weapon_idx_lst, tags_chosen) in enumerate(zip(best_weapon_indices_lists, tags_vis_list), 1):
                        target_weapons_chosen, nontarget_weapons_chosen = [], []
                        for weapon_idx in weapon_idx_lst:
                            weapon_chosen = weapons_list[weapon_idx]
                            if weapon_chosen in targets:
                                target_weapons_chosen.append(weapon_chosen)
                            else:
                                nontarget_weapons_chosen.append(weapon_chosen)
                        text.append(f'方案 [{idx}]：基础词条选择 [{'，'.join(tags_chosen[:-1])}] ，附加或技能词条选择 [{tags_chosen[-1]}] 可获得以下目标武器基质：\n')
                        for weapon in target_weapons_chosen:
                            text.append(f'{weapon} ({weapon_props[weapon][0]}*)'.ljust(20))
                            if self.check_inventory and self.inventory is not None:
                                text[-1] += ' ' * 10 + \
                                     f' - 武器{"已" if self.inventory['weapon_possessed'][weapon] else "未"}拥有，基质{"已" if self.inventory['weapon_core_possessed'][weapon] else "未"}拥有'
                        if nontarget_weapons_chosen:
                            text.append('\n同时可以获得以下其他武器：\n')
                            for weapon in nontarget_weapons_chosen:
                                text.append(f'{weapon} ({weapon_props[weapon][0]}*)'.ljust(20))
                                if self.check_inventory and self.inventory is not None:
                                    text[-1] += ' ' * 10 + \
                                        f' - 武器{"已" if self.inventory['weapon_possessed'][weapon] else "未"}拥有，基质{"已" if self.inventory['weapon_core_possessed'][weapon] else "未"}拥有'
                        text.append('*' * 50 + '\n')
                    text.append('-' * 100 + '\n')
            text = '\n'.join(text)
        self.text_edit.setText(text)

    def plan_weapon_no_core(self):
        """根据仓库中基质未拥有的情况计算最高效率的刷取计划"""
        self.load_inventory()

        # 更新 target_weapons_str -> 更新 target_weapons_str 的 line_edit 显示
        self.target_weapons_str = ' '.join(weapon for weapon in self.config['weapon_props'] if self.inventory['weapon_possessed'][weapon] and not self.inventory['weapon_core_possessed'][weapon])
        # 计算最优刷取计划
        self.plan()

    def plan_no_weapon_no_core(self):
        """根据仓库中武器已拥有，基质未拥有的情况计算最高效率的刷取计划"""
        self.load_inventory()

        # 更新 target_weapons_str -> 更新 target_weapons_str 的 line_edit 显示
        self.target_weapons_str = ' '.join(weapon for weapon in self.config['weapon_props'] if not self.inventory['weapon_core_possessed'][weapon])
        # 计算最优刷取计划
        self.plan()

    def init(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(50, 50, 50, 50)

        hbox = QHBoxLayout()

        vbox = QVBoxLayout()
        check_inventory_checkbox = QCheckBox('检查仓储', parent=self)
        check_inventory_checkbox.clicked.connect(lambda: setattr(self, 'check_inventory', check_inventory_checkbox.isChecked()))  # 更新 check_inventory 属性
        plan_weapon_no_core_btn = QPushButton('补图鉴', parent=self)
        plan_weapon_no_core_btn.setEnabled(False)
        plan_weapon_no_core_btn.clicked.connect(self.plan_weapon_no_core)
        plan_no_weapon_no_core_btn = QPushButton('随便刷', parent=self)
        plan_no_weapon_no_core_btn.setEnabled(False)  # 默认不可使用
        plan_no_weapon_no_core_btn.clicked.connect(self.plan_no_weapon_no_core)
        check_inventory_checkbox.stateChanged.connect(lambda: plan_weapon_no_core_btn.setEnabled(check_inventory_checkbox.isChecked()))  # 状态随检查仓储的按钮变化，只有在 检查仓储 启用时才能使用 补图鉴
        check_inventory_checkbox.stateChanged.connect(lambda: plan_no_weapon_no_core_btn.setEnabled(check_inventory_checkbox.isChecked()))  # 状态随检查仓储的按钮变化，只有在 检查仓储 启用时才能使用 随便刷
        vbox.addWidget(check_inventory_checkbox)
        vbox.addSpacing(5)
        vbox.addWidget(plan_weapon_no_core_btn)
        vbox.addSpacing(5)
        vbox.addWidget(plan_no_weapon_no_core_btn)

        hbox.addLayout(vbox)
        hbox.addSpacing(5)
        hbox.addWidget(VDividerWidget(parent=self))
        hbox.addSpacing(5)
        hbox.addWidget(QLabel('想要刷取的武器：\n（多个武器之间需用空格或中英文逗号分隔）', parent=self))
        line_edit = QLineEdit(parent=self)
        line_edit.textChanged.connect(lambda: setattr(self, 'target_weapons_str', line_edit.text()))  # 更新 target_weapons_str
        plan_weapon_no_core_btn.clicked.connect(lambda: line_edit.setText(self.target_weapons_str))  # 更新 target_weapons_str 的 line_edit 
        plan_no_weapon_no_core_btn.clicked.connect(lambda: line_edit.setText(self.target_weapons_str))  # 更新 target_weapons_str 的 line_edit 
        hbox.addSpacing(5)
        hbox.addWidget(line_edit)
        hbox.addSpacing(10)
        confirm_button = QPushButton('确定', parent=self)
        confirm_button.clicked.connect(self.plan)
        hbox.addWidget(confirm_button)

        main_layout.addLayout(hbox)

        self.text_edit = QTextEdit(parent=self, readOnly=True)
        main_layout.addWidget(self.text_edit)

        self.setLayout(main_layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.tab_widget = QTabWidget()

        self.init_ui()

    def load_config(self):
        if not (get_root_path() / 'config.json').exists():
            QMessageBox.critical(self, 'config.json 文件不存在', 'config.json 文件缺失！')
            return
        with open(get_root_path() / 'config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    
    def init_ui(self):
        self.resize(1200, 800)

        center_point = QApplication.primaryScreen().availableGeometry().center()
        frame_geom = self.frameGeometry()
        frame_geom.moveCenter(center_point)
        self.move(frame_geom.topLeft())

        self.setWindowTitle('终末地武器基质 app')

        # 布局
        # 基质刷取建议
        self.tab_widget.addTab(WeaponCorePlannerWidget(parent=self, config=self.config), '基质刷取推荐')

        # 武器基质检查
        self.tab_widget.addTab(WeaponCheckerWidget(parent=self, config=self.config), '基质检查')

        self.setCentralWidget(self.tab_widget)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
