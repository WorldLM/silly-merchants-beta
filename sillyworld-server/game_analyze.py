import json
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np
from game_record import GameRecord


class GameAnalyzer:
    """游戏分析工具，用于分析多轮游戏数据"""

    def __init__(self, record_dir="game_records"):
        """初始化游戏分析器
        
        Args:
            record_dir: 游戏记录目录
        """
        self.game_record = GameRecord(record_dir)
        self.analysis_dir = Path("analysis_results")
        self.analysis_dir.mkdir(exist_ok=True)

    def analyze_all_games(self) -> Dict[str, Any]:
        """分析所有游戏记录
        
        Returns:
            Dict: 分析结果
        """
        all_records = self.game_record.list_game_records()

        if not all_records:
            return {"error": "没有找到游戏记录"}

        # 游戏统计
        game_count = len(all_records)
        total_rounds = 0
        total_actions = 0

        # 玩家统计
        player_stats = defaultdict(lambda: {
            "games_played": 0,
            "wins": 0,
            "avg_final_balance": 0,
            "total_persuasions": 0,
            "successful_persuasions": 0,
            "items_purchased": defaultdict(int),
            "items_used": defaultdict(int)
        })

        # 道具统计
        item_stats = defaultdict(lambda: {
            "total_purchased": 0,
            "total_used": 0,
            "success_rate": 0,
            "avg_effect": 0
        })

        # 收集所有游戏数据
        all_game_data = []
        for record_file in all_records:
            try:
                game_data = self.game_record.load_game_record(record_file)
                all_game_data.append(game_data)

                # 基本游戏信息
                total_rounds += game_data.get("total_rounds", 0)
                winner = game_data.get("winner", "未知")

                # 玩家信息
                for player in game_data.get("players", []):
                    player_name = player.get("name", "未知玩家")
                    player_stats[player_name]["games_played"] += 1

                    if player_name == winner:
                        player_stats[player_name]["wins"] += 1

                    player_stats[player_name]["avg_final_balance"] += player.get("final_balance", 0)

                # 回合信息
                for round_data in game_data.get("rounds", []):
                    for phase in round_data.get("phases", []):
                        for action in phase.get("actions", []):
                            total_actions += 1
                            action_type = action.get("action_type", "")
                            player_name = action.get("player_name", "未知玩家")

                            if action_type == "persuasion":
                                player_stats[player_name]["total_persuasions"] += 1
                                if action.get("success", False):
                                    player_stats[player_name]["successful_persuasions"] += 1

                            elif action_type == "purchase":
                                item_type = action.get("item_type", "未知道具")
                                player_stats[player_name]["items_purchased"][item_type] += 1
                                item_stats[item_type]["total_purchased"] += 1

                            elif action_type == "item_use":
                                item_type = action.get("item_type", "未知道具")
                                player_stats[player_name]["items_used"][item_type] += 1
                                item_stats[item_type]["total_used"] += 1

            except Exception as e:
                print(f"分析文件 {record_file} 时出错: {str(e)}")

        # 计算平均值和百分比
        for player_name, stats in player_stats.items():
            if stats["games_played"] > 0:
                stats["avg_final_balance"] /= stats["games_played"]
                stats["win_rate"] = stats["wins"] / stats["games_played"] * 100

            if stats["total_persuasions"] > 0:
                stats["persuasion_success_rate"] = stats["successful_persuasions"] / stats["total_persuasions"] * 100

        # 生成分析结果
        result = {
            "game_stats": {
                "total_games": game_count,
                "total_rounds": total_rounds,
                "avg_rounds_per_game": total_rounds / game_count if game_count > 0 else 0,
                "total_actions": total_actions
            },
            "player_stats": dict(player_stats),
            "item_stats": dict(item_stats)
        }

        # 保存分析结果
        timestamp = os.path.basename(self.analysis_dir)
        result_file = self.analysis_dir / f"analysis_result_{timestamp}.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result

    def generate_player_matchup_analysis(self) -> Dict[str, Dict[str, Any]]:
        """生成玩家之间的对决分析
        
        Returns:
            Dict: 玩家对决分析结果
        """
        all_records = self.game_record.list_game_records()

        if not all_records:
            return {"error": "没有找到游戏记录"}

        # 玩家对决统计
        matchups = defaultdict(lambda: defaultdict(lambda: {
            "games": 0,
            "wins": 0,
            "total_persuasions": 0,
            "successful_persuasions": 0
        }))

        # 收集所有游戏数据
        for record_file in all_records:
            try:
                game_data = self.game_record.load_game_record(record_file)

                # 获取玩家名单
                players = [p.get("name", "未知玩家") for p in game_data.get("players", [])]
                winner = game_data.get("winner", "未知")

                # 记录每对玩家的对决情况
                for i, player1 in enumerate(players):
                    for j, player2 in enumerate(players):
                        if i != j:  # 不统计自己对自己
                            matchups[player1][player2]["games"] += 1

                            if player1 == winner:
                                matchups[player1][player2]["wins"] += 1

                # 记录每个玩家对其他玩家的说服情况
                for round_data in game_data.get("rounds", []):
                    for phase in round_data.get("phases", []):
                        for action in phase.get("actions", []):
                            if action.get("action_type") == "persuasion":
                                player_name = action.get("player_name", "未知玩家")
                                target = action.get("target", "未知玩家")

                                if player_name in players and target in players:
                                    matchups[player_name][target]["total_persuasions"] += 1
                                    if action.get("success", False):
                                        matchups[player_name][target]["successful_persuasions"] += 1

            except Exception as e:
                print(f"分析文件 {record_file} 时出错: {str(e)}")

        # 计算胜率和说服成功率
        result = {}
        for player1, opponents in matchups.items():
            result[player1] = {}
            for player2, stats in opponents.items():
                result[player1][player2] = {
                    **stats,
                    "win_rate": stats["wins"] / stats["games"] * 100 if stats["games"] > 0 else 0,
                    "persuasion_success_rate": stats["successful_persuasions"] / stats["total_persuasions"] * 100
                    if stats["total_persuasions"] > 0 else 0
                }

        # 保存对决分析结果
        timestamp = os.path.basename(self.analysis_dir)
        matchup_file = self.analysis_dir / f"matchup_analysis_{timestamp}.json"
        with open(matchup_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result

    def plot_player_win_rates(self, save_to_file=True) -> None:
        """绘制玩家胜率图表
        
        Args:
            save_to_file: 是否保存到文件
        """
        try:
            # 导入matplotlib，如果不可用则跳过
            import matplotlib.pyplot as plt

            analysis_result = self.analyze_all_games()
            player_stats = analysis_result.get("player_stats", {})

            if not player_stats:
                print("没有可用的玩家数据")
                return

            # 提取玩家名称和胜率
            player_names = []
            win_rates = []
            persuasion_rates = []

            for player_name, stats in player_stats.items():
                player_names.append(player_name)
                win_rates.append(stats.get("win_rate", 0))
                persuasion_rates.append(stats.get("persuasion_success_rate", 0))

            # 绘制胜率图表
            plt.figure(figsize=(12, 6))

            x = np.arange(len(player_names))
            width = 0.35

            plt.bar(x - width / 2, win_rates, width, label='胜率 (%)')
            plt.bar(x + width / 2, persuasion_rates, width, label='说服成功率 (%)')

            plt.xlabel('玩家')
            plt.ylabel('百分比 (%)')
            plt.title('玩家胜率和说服成功率分析')
            plt.xticks(x, player_names, rotation=45)
            plt.legend()

            plt.tight_layout()

            if save_to_file:
                plot_file = self.analysis_dir / "player_win_rates.png"
                plt.savefig(plot_file)
                print(f"图表已保存到: {plot_file}")
            else:
                plt.show()

            plt.close()

        except ImportError:
            print("绘图需要matplotlib库，请先安装: pip install matplotlib")

    def plot_item_usage(self, save_to_file=True) -> None:
        """绘制道具使用统计图表
        
        Args:
            save_to_file: 是否保存到文件
        """
        try:
            # 导入matplotlib，如果不可用则跳过
            import matplotlib.pyplot as plt

            analysis_result = self.analyze_all_games()
            item_stats = analysis_result.get("item_stats", {})

            if not item_stats:
                print("没有可用的道具数据")
                return

            # 提取道具名称和使用数据
            item_names = []
            purchased = []
            used = []

            for item_name, stats in item_stats.items():
                item_names.append(item_name)
                purchased.append(stats.get("total_purchased", 0))
                used.append(stats.get("total_used", 0))

            # 绘制道具统计图表
            plt.figure(figsize=(12, 6))

            x = np.arange(len(item_names))
            width = 0.35

            plt.bar(x - width / 2, purchased, width, label='购买次数')
            plt.bar(x + width / 2, used, width, label='使用次数')

            plt.xlabel('道具类型')
            plt.ylabel('次数')
            plt.title('道具购买和使用统计')
            plt.xticks(x, item_names, rotation=45)
            plt.legend()

            plt.tight_layout()

            if save_to_file:
                plot_file = self.analysis_dir / "item_usage_stats.png"
                plt.savefig(plot_file)
                print(f"图表已保存到: {plot_file}")
            else:
                plt.show()

            plt.close()

        except ImportError:
            print("绘图需要matplotlib库，请先安装: pip install matplotlib")

    def print_analysis_summary(self) -> None:
        """打印分析摘要"""
        analysis_result = self.analyze_all_games()

        print("\n===== 游戏分析摘要 =====")

        # 游戏统计
        game_stats = analysis_result.get("game_stats", {})
        print(f"\n游戏总数: {game_stats.get('total_games', 0)}")
        print(f"总回合数: {game_stats.get('total_rounds', 0)}")
        print(f"平均每局回合数: {game_stats.get('avg_rounds_per_game', 0):.2f}")
        print(f"总行动数: {game_stats.get('total_actions', 0)}")

        # 玩家统计
        player_stats = analysis_result.get("player_stats", {})
        print("\n玩家表现:")

        # 按胜率排序
        sorted_players = sorted(player_stats.items(),
                                key=lambda x: x[1].get("win_rate", 0),
                                reverse=True)

        for player_name, stats in sorted_players:
            print(f"\n  {player_name}:")
            print(f"    参与游戏: {stats.get('games_played', 0)} 局")
            print(f"    获胜: {stats.get('wins', 0)} 局 (胜率: {stats.get('win_rate', 0):.2f}%)")
            print(f"    平均最终余额: {stats.get('avg_final_balance', 0):.2f} 代币")
            print(f"    说服尝试: {stats.get('total_persuasions', 0)} 次")
            print(
                f"    说服成功: {stats.get('successful_persuasions', 0)} 次 (成功率: {stats.get('persuasion_success_rate', 0):.2f}%)")

            print("    购买道具:")
            for item, count in stats.get("items_purchased", {}).items():
                print(f"      - {item}: {count} 次")

            print("    使用道具:")
            for item, count in stats.get("items_used", {}).items():
                print(f"      - {item}: {count} 次")

        # 道具统计
        item_stats = analysis_result.get("item_stats", {})
        print("\n道具统计:")

        for item_name, stats in item_stats.items():
            print(f"\n  {item_name}:")
            print(f"    购买次数: {stats.get('total_purchased', 0)}")
            print(f"    使用次数: {stats.get('total_used', 0)}")


if __name__ == "__main__":
    analyzer = GameAnalyzer()
    analyzer.print_analysis_summary()

    try:
        analyzer.plot_player_win_rates()
        analyzer.plot_item_usage()
    except Exception as e:
        print(f"绘制图表时出错: {str(e)}")

    # 生成玩家对决分析
    matchup_analysis = analyzer.generate_player_matchup_analysis()
    print("\n玩家对决分析已生成")
