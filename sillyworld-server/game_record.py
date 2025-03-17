import json
import os
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

class GameRecord:
    """游戏记录管理器，负责保存和读取游戏记录"""
    
    def __init__(self, record_dir="game_records"):
        """初始化游戏记录管理器
        
        Args:
            record_dir: 游戏记录保存目录
        """
        self.record_dir = Path(record_dir)
        self.record_dir.mkdir(exist_ok=True)
        
    def save_game_record(self, game_data: Dict[str, Any]) -> str:
        """保存游戏记录
        
        Args:
            game_data: 游戏数据字典
            
        Returns:
            str: 保存的文件路径
        """
        game_id = game_data.get("game_id", f"game_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{game_id}_{timestamp}.json"
        filepath = self.record_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(game_data, f, ensure_ascii=False, indent=2)
            
        return str(filepath)
    
    def load_game_record(self, filename: str) -> Dict[str, Any]:
        """读取游戏记录
        
        Args:
            filename: 文件名
            
        Returns:
            Dict: 游戏数据字典
        """
        filepath = self.record_dir / filename
        
        with open(filepath, "r", encoding="utf-8") as f:
            game_data = json.load(f)
            
        return game_data
    
    def list_game_records(self) -> List[str]:
        """列出所有游戏记录
        
        Returns:
            List[str]: 游戏记录文件名列表
        """
        return [f.name for f in self.record_dir.glob("*.json")]
    
    def get_game_summary(self, filename: str) -> Dict[str, Any]:
        """获取游戏摘要信息
        
        Args:
            filename: 文件名
            
        Returns:
            Dict: 游戏摘要
        """
        game_data = self.load_game_record(filename)
        
        summary = {
            "game_id": game_data.get("game_id", "未知"),
            "start_time": game_data.get("start_time", "未知"),
            "end_time": game_data.get("end_time", "未知"),
            "total_rounds": game_data.get("total_rounds", 0),
            "winner": game_data.get("winner", "未知"),
            "player_count": len(game_data.get("players", [])),
            "players": [p.get("name", "未知玩家") for p in game_data.get("players", [])]
        }
        
        return summary
    
    def export_readable_record(self, filename: str, output_dir="readable_records") -> str:
        """导出可读的游戏记录
        
        Args:
            filename: 游戏记录文件名
            output_dir: 输出目录
            
        Returns:
            str: 输出文件路径
        """
        Path(output_dir).mkdir(exist_ok=True)
        game_data = self.load_game_record(filename)
        
        output_filename = filename.replace(".json", ".txt")
        output_path = Path(output_dir) / output_filename
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"游戏ID: {game_data.get('game_id', '未知')}\n")
            f.write(f"开始时间: {game_data.get('start_time', '未知')}\n")
            f.write(f"结束时间: {game_data.get('end_time', '未知')}\n")
            f.write(f"总轮数: {game_data.get('total_rounds', 0)}\n")
            f.write(f"获胜者: {game_data.get('winner', '未知')}\n\n")
            
            f.write("玩家信息:\n")
            for player in game_data.get("players", []):
                f.write(f"  - {player.get('name', '未知玩家')}: 最终余额 {player.get('final_balance', 0)} 代币\n")
            
            f.write("\n游戏回合记录:\n")
            for round_idx, round_data in enumerate(game_data.get("rounds", []), 1):
                f.write(f"\n==== 第 {round_idx} 轮 ====\n")
                
                # 阶段记录
                for phase in round_data.get("phases", []):
                    phase_name = phase.get("phase_name", "未知阶段")
                    f.write(f"\n-- {phase_name} --\n")
                    
                    # 记录各种行动
                    for action in phase.get("actions", []):
                        action_type = action.get("action_type", "未知行动")
                        player_name = action.get("player_name", "未知玩家")
                        
                        if action_type == "item_use":
                            item_type = action.get("item_type", "未知道具")
                            target = action.get("target", "无目标")
                            f.write(f"{player_name} 使用了 {item_type} 对象为 {target}\n")
                        
                        elif action_type == "persuasion":
                            target = action.get("target", "无目标")
                            amount = action.get("amount", 0)
                            success = action.get("success", False)
                            f.write(f"{player_name} 尝试说服 {target} 转账 {amount} 代币, ")
                            f.write("成功\n" if success else "失败\n")
                        
                        elif action_type == "purchase":
                            item_type = action.get("item_type", "未知道具")
                            cost = action.get("cost", 0)
                            f.write(f"{player_name} 购买了 {item_type}, 花费 {cost} 代币\n")
                
                # 轮次结束状态
                f.write("\n轮末状态:\n")
                for player_state in round_data.get("end_state", {}).get("players", []):
                    player_name = player_state.get("name", "未知玩家")
                    balance = player_state.get("balance", 0)
                    items = player_state.get("items", [])
                    f.write(f"  - {player_name}: {balance} 代币, 持有道具: {', '.join(items) if items else '无'}\n")
                
                f.write(f"奖池: {round_data.get('end_state', {}).get('prize_pool', 0)} 代币\n")
            
        return str(output_path) 