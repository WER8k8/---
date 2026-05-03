const { sequelize, models } = require('../config/database');
const PlatformAccount = models.PlatformAccount;
const PublishTask = models.PublishTask;
const GeneratedArticle = models.GeneratedArticle;

class PlatformAdapter {
  constructor(account) {
    this.account = account;
    this.platformName = account.platform_name;
  }

  async publish(article) {
    const adapter = this.getAdapter();
    return await adapter.publish(article);
  }

  getAdapter() {
    const adapters = {
      '百度贴吧': new TiebaAdapter(this.account),
      '知乎': new ZhihuAdapter(this.account),
      '小红书': new XiaohongshuAdapter(this.account),
      '抖音': new DouyinAdapter(this.account),
      '微信公众号': new WechatAdapter(this.account),
      '新浪博客': new SinaBlogAdapter(this.account),
      'CSDN': new CSDNAdapter(this.account),
      '简书': new JianshuAdapter(this.account)
    };
    
    return adapters[this.platformName] || new DefaultAdapter(this.account);
  }
}

class TiebaAdapter {
  constructor(account) {
    this.account = account;
  }

  async publish(article) {
    await this.delay(1000 + Math.random() * 2000);
    const success = Math.random() > 0.1;
    
    return {
      success,
      platform: '百度贴吧',
      message: success ? '发布成功' : '发布失败',
      url: success ? `https://tieba.baidu.com/p/${Date.now()}` : null
    };
  }

  async delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

class ZhihuAdapter {
  constructor(account) {
    this.account = account;
  }

  async publish(article) {
    await this.delay(1500 + Math.random() * 2500);
    const success = Math.random() > 0.15;
    
    return {
      success,
      platform: '知乎',
      message: success ? '发布成功' : '发布失败',
      url: success ? `https://zhihu.com/question/${Date.now()}` : null
    };
  }

  async delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

class XiaohongshuAdapter {
  constructor(account) {
    this.account = account;
  }

  async publish(article) {
    await this.delay(1200 + Math.random() * 1800);
    const success = Math.random() > 0.12;
    
    return {
      success,
      platform: '小红书',
      message: success ? '发布成功' : '发布失败',
      url: success ? `https://xiaohongshu.com/item/${Date.now()}` : null
    };
  }

  async delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

class DouyinAdapter {
  constructor(account) {
    this.account = account;
  }

  async publish(article) {
    await this.delay(2000 + Math.random() * 3000);
    const success = Math.random() > 0.2;
    
    return {
      success,
      platform: '抖音',
      message: success ? '发布成功' : '发布失败',
      url: success ? `https://douyin.com/video/${Date.now()}` : null
    };
  }

  async delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

class WechatAdapter {
  constructor(account) {
    this.account = account;
  }

  async publish(article) {
    await this.delay(1800 + Math.random() * 2200);
    const success = Math.random() > 0.1;
    
    return {
      success,
      platform: '微信公众号',
      message: success ? '发布成功' : '发布失败',
      url: success ? `https://mp.weixin.qq.com/s/${Date.now()}` : null
    };
  }

  async delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

class SinaBlogAdapter {
  constructor(account) {
    this.account = account;
  }

  async publish(article) {
    await this.delay(1000 + Math.random() * 1500);
    const success = Math.random() > 0.08;
    
    return {
      success,
      platform: '新浪博客',
      message: success ? '发布成功' : '发布失败',
      url: success ? `https://blog.sina.com.cn/s/${Date.now()}` : null
    };
  }

  async delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

class CSDNAdapter {
  constructor(account) {
    this.account = account;
  }

  async publish(article) {
    await this.delay(1300 + Math.random() * 1700);
    const success = Math.random() > 0.1;
    
    return {
      success,
      platform: 'CSDN',
      message: success ? '发布成功' : '发布失败',
      url: success ? `https://blog.csdn.net/article/${Date.now()}` : null
    };
  }

  async delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

class JianshuAdapter {
  constructor(account) {
    this.account = account;
  }

  async publish(article) {
    await this.delay(1100 + Math.random() * 1900);
    const success = Math.random() > 0.09;
    
    return {
      success,
      platform: '简书',
      message: success ? '发布成功' : '发布失败',
      url: success ? `https://jianshu.com/p/${Date.now()}` : null
    };
  }

  async delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

class DefaultAdapter {
  constructor(account) {
    this.account = account;
  }

  async publish(article) {
    await this.delay(1000 + Math.random() * 1000);
    const success = Math.random() > 0.1;
    
    return {
      success,
      platform: this.account.platform_name,
      message: success ? '发布成功' : '发布失败',
      url: success ? `https://example.com/article/${Date.now()}` : null
    };
  }

  async delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

const publishToPlatform = async (taskId) => {
  try {
    const task = await PublishTask.findByPk(taskId, {
      include: [
        { model: GeneratedArticle },
        { model: PlatformAccount }
      ]
    });

    if (!task) {
      throw new Error('任务不存在');
    }

    if (task.status !== 0) {
      throw new Error('任务状态不允许发布');
    }

    await task.update({ status: 1 });

    const adapter = new PlatformAdapter(task.PlatformAccount);
    const result = await adapter.publish(task.GeneratedArticle);

    await task.update({
      status: result.success ? 2 : 3,
      published_url: result.url,
      executed_at: new Date(),
      error_message: result.success ? null : result.message
    });

    return result;
  } catch (error) {
    console.error('发布任务执行失败:', error);
    
    await PublishTask.update({
      status: 3,
      executed_at: new Date(),
      error_message: error.message
    }, { where: { id: taskId } });

    throw error;
  }
};

const batchPublish = async (taskIds) => {
  const results = [];
  
  for (const taskId of taskIds) {
    try {
      const result = await publishToPlatform(taskId);
      results.push({ taskId, ...result });
    } catch (error) {
      results.push({ taskId, success: false, message: error.message });
    }
  }
  
  return results;
};

module.exports = {
  PlatformAdapter,
  publishToPlatform,
  batchPublish,
  TiebaAdapter,
  ZhihuAdapter,
  XiaohongshuAdapter,
  DouyinAdapter,
  WechatAdapter,
  SinaBlogAdapter,
  CSDNAdapter,
  JianshuAdapter
};