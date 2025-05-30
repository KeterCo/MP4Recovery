批量修复视频真实时长工具，用户仅需选择个文件夹，会自动扫描文件夹中的视频，有预览待处理视频列表的窗口界面。可自定义文件名后缀、同步修改同名.ass字幕文件和.xml配置文件。可选择是否递归处理文件夹下所有的视频文件。

python3.12.3,使用ffmpeg工具，目前仅支持mp4，win10可用。

判断：原视频大于100MB的视频增加了个判断逻辑，若生成的视频与原视频差距大于25%，则不处理该视频。

本地程序配置文件目录在：C:\Users\xxx\AppData\Local\Mp4recovery

![image](https://github.com/user-attachments/assets/772ccbb0-5169-48d2-b002-f906d577dc24)

![image](https://github.com/user-attachments/assets/f3c6e5aa-0638-4f7b-9797-329ee5680660)

![image](https://github.com/user-attachments/assets/d263175c-b144-4989-89a6-e4d763a0f0a2)

![image](https://github.com/user-attachments/assets/6f3afbe7-69ac-47eb-a74c-5645cc90a75f)

![image](https://github.com/user-attachments/assets/f4eff4b8-cb33-43df-8127-25c3eed25e3f)


处理前的某个视频时长为2:45（实际可能就几秒），大小为2.66 MB：
![image](https://github.com/user-attachments/assets/d20b1e97-d75b-4971-9032-d1ab891d2e19)
![image](https://github.com/user-attachments/assets/56006c19-a344-4c4d-9fbd-6657c864781f)

处理后该视频时长为16秒，大小为2.58MB：

![image](https://github.com/user-attachments/assets/b9d739ad-4a3b-4a91-aa4f-d6671520eaf1)

![image](https://github.com/user-attachments/assets/6f01e8e2-d73b-4cf4-a3a7-0c931a4d4ccb)
