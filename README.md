批量修复视频真实时长工具，用户仅需选择个文件夹，会自动扫描文件夹中的视频，有预览待处理视频列表的窗口界面。可自定义文件名后缀、同步修改同名.ass字幕文件和.xml配置文件。可选择是否递归处理文件夹下所有的视频文件。

python3.12.3，使用ffmpeg工具，目前仅支持mp4，环境win10。

判断：大于100MB的原视频，若生成的视频与原视频差距大于25%，则不处理该原视频。

本地程序配置文件目录在：C:\Users\xxx\AppData\Local\Mp4recovery

**处理前的某个视频时长为10:05（实际可能就几秒），大小为4.51MB：**
![image](https://github.com/user-attachments/assets/8bcc22ae-d129-41c6-971d-a0a8b794ebb6)
![image](https://github.com/user-attachments/assets/21e1ea2b-43a8-4abf-9748-d8296fb1ae17)



**处理后该视频时长为18秒，大小为4.26MB：**
![image](https://github.com/user-attachments/assets/6421ba9f-fe74-4282-be7e-1ccce180fe50)
![image](https://github.com/user-attachments/assets/ecb0c36e-a62d-4a70-afd4-b9a01976011f)

**主界面：**
![image](https://github.com/user-attachments/assets/78d1b193-3cc3-45e8-82aa-a9a2f1cb8282)


**示例需要处理的文件夹目录（mp4）：**

![image](https://github.com/user-attachments/assets/2b74158d-0923-4fac-bdc4-c760346469f1)

**主文件夹（示例里所有文件均包含字幕和配置文件）：**
![image](https://github.com/user-attachments/assets/8d1af0ff-dacd-476e-af64-6504f2cb1493)

**找到23个mp4视频：**
![image](https://github.com/user-attachments/assets/a103c1d4-e259-4fb2-b56f-37c2bc926597)

**处理结果：**
![image](https://github.com/user-attachments/assets/af06d1a3-bc4c-4f72-80d0-74ff69389b18)










