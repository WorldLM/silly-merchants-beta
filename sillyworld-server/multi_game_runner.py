import argparse
import asyncio
import time
from pathlib import Path
from datetime import datetime
import json
from typing import List, Dict, Any, Optional

from game import Game, GameState
from ai import AIPlayer
from game_record import GameRecord
from game_analyze import GameAnalyzer


class MultiGameRunner:
    """多轮游戏测试框架，用于批量运行游戏测试"""

    def __init__(self,
                 num_games: int = 10,
                 players_per_game: int = 4,
                 rounds_per_game: int = 8,
                 initial_balance: int = 100,
                 output_dir: str = "multi_game_results"):
        """初始化多轮游戏测试框架
        
        Args:
            num_games: 运行的游戏局数
            players_per_game: 每局游戏的玩家数
            rounds_per_game: 每局游戏的回合数
            initial_balance: 初始代币数量
            output_dir: 输出目录
        """
        self.num_games = num_games
        self.players_per_game = players_per_game
        self.rounds_per_game = rounds_per_game
        self.initial_balance = initial_balance
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.game_record = GameRecord("game_records")

        # AI玩家配置，可以根据需要修改
        self.player_configs = [
            {"name": "策略家", "personality": "你是一个精明的策略家，善于计算和分析。你总是尝试做出最优决策。"},
            {"name": "冒险家", "personality": "你是一个喜欢冒险的玩家，偏好高风险高回报的策略。你愿意尝试新策略。"},
            {"name": "保守派", "personality": "你是一个谨慎的玩家，不喜欢冒险。你倾向于保守策略，优先保住自己的代币。"},
            {"name": "均衡者", "personality": "你是一个平衡型玩家，追求稳健的游戏风格。你会根据局势调整策略。"},
            {"name": "欺诈师", "personality": "你是一个擅长欺骗的玩家，喜欢误导他人。你善于隐藏自己的真实意图。"},
            {"name": "合作者", "personality": "你是一个倾向于合作的玩家，愿意与他人建立互利关系。你相信互惠互利。"},
            {"name": "观察者",
             "personality": "你是一个善于观察的玩家，会仔细分析其他玩家的行为模式。你有很强的适应能力。"},
            {"name": "激进派", "personality": "你是一个激进的玩家，喜欢采取主动并施加压力。你偏好攻击性策略。"}
        ]

    async def run_single_game(self, game_id: str) -> Dict[str, Any]:
        """运行单局游戏
        
        Args:
            game_id: 游戏ID
            
        Returns:
            Dict: 游戏结果
        """
        # 确保每次游戏有足够的玩家配置
        if len(self.player_configs) < self.players_per_game:
            raise ValueError(f"玩家配置不足，需要至少 {self.players_per_game} 个配置")

        # 随机选择玩家配置
        import random
        selected_configs = random.sample(self.player_configs, self.players_per_game)

        # 创建玩家列表
        players = []
        for config in selected_configs:
            player = AIPlayer(
                player_id=f"player_{len(players) + 1}",
                name=config["name"],
                personality=config["personality"]
            )
            players.append(player)

        # 创建游戏实例
        game = Game(
            game_id=game_id,
            max_rounds=self.rounds_per_game,
            initial_balance=self.initial_balance
        )

        # 添加玩家
        for player in players:
            game.add_player(player)

        # 记录游戏过程
        game_data = {
            "game_id": game_id,
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "players": [{"id": p.player_id, "name": p.name, "personality": p.personality} for p in players],
            "max_rounds": self.rounds_per_game,
            "initial_balance": self.initial_balance,
            "rounds": []
        }

        print(f"开始游戏 {game_id}，玩家：{[p.name for p in players]}")

        # 开始游戏
        await game.start_game()

        # 游戏回合循环
        current_round = 0
        while not game.is_game_over():
            current_round += 1
            print(f"游戏 {game_id} - 第 {current_round} 回合开始")

            # 回合数据
            round_data = {
                "round_number": current_round,
                "phases": [],
                "end_state": None
            }

            # 道具阶段
            phase_data = {"phase_name": "道具阶段", "actions": []}
            await game.item_phase()

            # 记录道具使用行为
            for player_id, actions in game.round_actions.items():
                for action in actions:
                    if action.action_type == "use_item":
                        player = game.get_player_by_id(player_id)
                        phase_data["actions"].append({
                            "action_type": "item_use",
                            "player_id": player_id,
                            "player_name": player.name,
                            "item_type": action.item_type,
                            "target": action.target_player
                        })

            round_data["phases"].append(phase_data)

            # 说服阶段
            phase_data = {"phase_name": "说服阶段", "actions": []}
            await game.persuasion_phase()

            # 记录说服行为
            for player_id, actions in game.round_actions.items():
                for action in actions:
                    if action.action_type == "persuade":
                        player = game.get_player_by_id(player_id)
                        target_player = game.get_player_by_id(action.target_player)
                        phase_data["actions"].append({
                            "action_type": "persuasion",
                            "player_id": player_id,
                            "player_name": player.name,
                            "target": target_player.name,
                            "amount": action.amount,
                            "success": action.success
                        })

            round_data["phases"].append(phase_data)

            # 结算阶段
            phase_data = {"phase_name": "结算阶段", "actions": []}
            await game.settlement_phase()

            # 记录购买行为
            for player_id, actions in game.round_actions.items():
                for action in actions:
                    if action.action_type == "purchase":
                        player = game.get_player_by_id(player_id)
                        phase_data["actions"].append({
                            "action_type": "purchase",
                            "player_id": player_id,
                            "player_name": player.name,
                            "item_type": action.item_type,
                            "cost": action.amount
                        })

            round_data["phases"].append(phase_data)

            # 记录回合结束状态
            game_state = game.get_game_state()
            round_data["end_state"] = {
                "current_round": game_state.current_round,
                "phase": game_state.phase,
                "prize_pool": game_state.prize_pool,
                "players": [
                    {
                        "id": p.player_id,
                        "name": p.name,
                        "balance": p.balance,
                        "items": p.items
                    } for p in game_state.players
                ]
            }

            game_data["rounds"].append(round_data)

            # 进入下一回合
            await game.next_round()

            print(f"游戏 {game_id} - 第 {current_round} 回合结束")

        # 游戏结束，记录结果
        game_result = game.get_game_result()
        winner = game.get_player_by_id(game_result.winner_id)

        game_data["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        game_data["total_rounds"] = game_result.total_rounds
        game_data["winner"] = winner.name
        game_data["winner_id"] = winner.player_id
        game_data["final_balances"] = {
            p.player_id: p.balance for p in game.get_game_state().players
        }

        # 记录玩家最终状态
        for player in game_data["players"]:
            player_id = player["id"]
            player_obj = game.get_player_by_id(player_id)
            player["final_balance"] = player_obj.balance
            player["final_items"] = player_obj.items

        print(f"游戏 {game_id} 结束，获胜者：{winner.name}，最终余额：{winner.balance}")

        # 保存游戏记录
        self.game_record.save_game_record(game_data)

        return game_data

    async def run_all_games(self) -> List[Dict[str, Any]]:
        """运行所有游戏测试
        
        Returns:
            List[Dict]: 所有游戏结果
        """
        results = []

        for i in range(1, self.num_games + 1):
            game_id = f"multi_game_{datetime.now().strftime('%Y%m%d')}_{i}"
            try:
                result = await self.run_single_game(game_id)
                results.append(result)
            except Exception as e:
                print(f"游戏 {game_id} 运行出错: {str(e)}")

        # 生成统计报告
        self.generate_summary_report(results)

        return results

    def generate_summary_report(self, results: List[Dict[str, Any]]) -> None:
        """生成汇总报告
        
        Args:
            results: 游戏结果列表
        """
        if not results:
            print("没有游戏结果可供分析")
            return

        # 使用GameAnalyzer分析结果
        analyzer = GameAnalyzer("game_records")

        # 打印分析摘要
        analyzer.print_analysis_summary()

        # 生成图表
        try:
            analyzer.plot_player_win_rates()
            analyzer.plot_item_usage()
        except Exception as e:
            print(f"生成图表时出错: {str(e)}")

        # 生成玩家对决分析
        matchup_analysis = analyzer.generate_player_matchup_analysis()

        # 保存简单的摘要报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = self.output_dir / f"summary_report_{timestamp}.json"

        summary = {
            "num_games": len(results),
            "timestamp": timestamp,
            "games": [
                {
                    "game_id": r["game_id"],
                    "winner": r["winner"],
                    "total_rounds": r["total_rounds"],
                    "player_count": len(r["players"])
                } for r in results
            ]
        }

        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"汇总报告已保存到: {summary_file}")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="多轮游戏测试框架")
    parser.add_argument("-n", "--num-games", type=int, default=10, help="要运行的游戏局数")
    parser.add_argument("-p", "--players", type=int, default=4, help="每局游戏的玩家数")
    parser.add_argument("-r", "--rounds", type=int, default=8, help="每局游戏的回合数")
    parser.add_argument("-b", "--balance", type=int, default=100, help="初始代币数量")
    parser.add_argument("-o", "--output", type=str, default="multi_game_results", help="输出目录")

    return parser.parse_args()


async def main():
    """主函数"""
    args = parse_args()

    runner = MultiGameRunner(
        num_games=args.num_games,
        players_per_game=args.players,
        rounds_per_game=args.rounds,
        initial_balance=args.balance,
        output_dir=args.output
    )

    start_time = time.time()
    print(f"开始运行 {args.num_games} 局游戏测试")

    results = await runner.run_all_games()

    end_time = time.time()
    duration = end_time - start_time

    print(f"测试完成，共运行 {len(results)} 局游戏")
    print(f"总用时: {duration:.2f} 秒，平均每局: {duration / len(results):.2f} 秒")


if __name__ == "__main__":
    asyncio.run(main())
