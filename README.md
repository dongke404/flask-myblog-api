# flask-myblog-api

## 博客项目的接口代码

根据文档自动安装  
pip3 install -r requirements.txt  
运行  

# 第一次运行创建自增队列来创建自增id
```bash
python create.py 
```

```bash
python manage.py runserver
#或
gunicorn -w 4 -b 0.0.0.0:5000 manage:app
```

此代码配合nuxt3-blog和vue-blog-manage使用,开发部署请修改配置
[nuxt-myblog](https://github.com/dongke404/nuxt-myblog)
[vue-myblog-manage](https://github.com/dongke404/vue-myblog-manage)

详细教程搭建个人站点请阅读我的博客 <https://kedong.me/article/80>
