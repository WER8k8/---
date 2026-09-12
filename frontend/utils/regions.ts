// 常用省份及城市数据
export interface City {
  name: string
}

export interface Province {
  name: string
  cities: City[]
}

export const regions: Province[] = [
  {
    name: '北京',
    cities: [{ name: '朝阳区' }, { name: '海淀区' }, { name: '丰台区' }, { name: '通州区' }, { name: '大兴区' }, { name: '昌平区' }, { name: '顺义区' }, { name: '房山区' }]
  },
  {
    name: '上海',
    cities: [{ name: '浦东新区' }, { name: '闵行区' }, { name: '宝山区' }, { name: '嘉定区' }, { name: '松江区' }, { name: '青浦区' }, { name: '奉贤区' }, { name: '崇明区' }]
  },
  {
    name: '天津',
    cities: [{ name: '滨海新区' }, { name: '武清区' }, { name: '西青区' }, { name: '北辰区' }, { name: '东丽区' }, { name: '津南区' }]
  },
  {
    name: '重庆',
    cities: [{ name: '渝北区' }, { name: '九龙坡区' }, { name: '沙坪坝区' }, { name: '巴南区' }, { name: '江津区' }, { name: '永川区' }, { name: '合川区' }, { name: '万州区' }]
  },
  {
    name: '河北',
    cities: [{ name: '保定' }, { name: '石家庄' }, { name: '唐山' }, { name: '邯郸' }, { name: '廊坊' }, { name: '沧州' }, { name: '邢台' }, { name: '秦皇岛' }, { name: '张家口' }, { name: '衡水' }, { name: '承德' }]
  },
  {
    name: '山西',
    cities: [{ name: '太原' }, { name: '大同' }, { name: '长治' }, { name: '晋中' }, { name: '临汾' }, { name: '运城' }, { name: '晋城' }, { name: '忻州' }]
  },
  {
    name: '内蒙古',
    cities: [{ name: '呼和浩特' }, { name: '包头' }, { name: '鄂尔多斯' }, { name: '赤峰' }, { name: '通辽' }, { name: '呼伦贝尔' }]
  },
  {
    name: '辽宁',
    cities: [{ name: '沈阳' }, { name: '大连' }, { name: '鞍山' }, { name: '抚顺' }, { name: '锦州' }, { name: '营口' }, { name: '盘锦' }, { name: '丹东' }]
  },
  {
    name: '吉林',
    cities: [{ name: '长春' }, { name: '吉林' }, { name: '四平' }, { name: '延边' }, { name: '通化' }, { name: '松原' }]
  },
  {
    name: '黑龙江',
    cities: [{ name: '哈尔滨' }, { name: '大庆' }, { name: '齐齐哈尔' }, { name: '牡丹江' }, { name: '佳木斯' }, { name: '绥化' }]
  },
  {
    name: '江苏',
    cities: [{ name: '南京' }, { name: '苏州' }, { name: '无锡' }, { name: '常州' }, { name: '南通' }, { name: '徐州' }, { name: '扬州' }, { name: '盐城' }, { name: '镇江' }, { name: '泰州' }, { name: '淮安' }, { name: '连云港' }]
  },
  {
    name: '浙江',
    cities: [{ name: '杭州' }, { name: '宁波' }, { name: '温州' }, { name: '嘉兴' }, { name: '绍兴' }, { name: '金华' }, { name: '台州' }, { name: '湖州' }, { name: '丽水' }, { name: '舟山' }]
  },
  {
    name: '安徽',
    cities: [{ name: '合肥' }, { name: '芜湖' }, { name: '蚌埠' }, { name: '马鞍山' }, { name: '安庆' }, { name: '阜阳' }, { name: '滁州' }, { name: '六安' }, { name: '宿州' }, { name: '亳州' }]
  },
  {
    name: '福建',
    cities: [{ name: '福州' }, { name: '厦门' }, { name: '泉州' }, { name: '漳州' }, { name: '莆田' }, { name: '龙岩' }, { name: '三明' }, { name: '南平' }, { name: '宁德' }]
  },
  {
    name: '江西',
    cities: [{ name: '南昌' }, { name: '赣州' }, { name: '九江' }, { name: '宜春' }, { name: '上饶' }, { name: '吉安' }, { name: '抚州' }, { name: '景德镇' }]
  },
  {
    name: '山东',
    cities: [{ name: '济南' }, { name: '青岛' }, { name: '烟台' }, { name: '潍坊' }, { name: '临沂' }, { name: '淄博' }, { name: '济宁' }, { name: '泰安' }, { name: '德州' }, { name: '威海' }, { name: '聊城' }, { name: '滨州' }]
  },
  {
    name: '河南',
    cities: [{ name: '郑州' }, { name: '洛阳' }, { name: '南阳' }, { name: '许昌' }, { name: '周口' }, { name: '新乡' }, { name: '安阳' }, { name: '开封' }, { name: '商丘' }, { name: '信阳' }, { name: '平顶山' }]
  },
  {
    name: '湖北',
    cities: [{ name: '武汉' }, { name: '宜昌' }, { name: '襄阳' }, { name: '荆州' }, { name: '黄冈' }, { name: '孝感' }, { name: '十堰' }, { name: '荆门' }, { name: '鄂州' }]
  },
  {
    name: '湖南',
    cities: [{ name: '长沙' }, { name: '株洲' }, { name: '湘潭' }, { name: '衡阳' }, { name: '岳阳' }, { name: '常德' }, { name: '邵阳' }, { name: '郴州' }, { name: '益阳' }]
  },
  {
    name: '广东',
    cities: [{ name: '广州' }, { name: '深圳' }, { name: '东莞' }, { name: '佛山' }, { name: '惠州' }, { name: '中山' }, { name: '珠海' }, { name: '江门' }, { name: '汕头' }, { name: '湛江' }, { name: '肇庆' }, { name: '茂名' }]
  },
  {
    name: '广西',
    cities: [{ name: '南宁' }, { name: '柳州' }, { name: '桂林' }, { name: '玉林' }, { name: '梧州' }, { name: '北海' }, { name: '贵港' }]
  },
  {
    name: '海南',
    cities: [{ name: '海口' }, { name: '三亚' }, { name: '儋州' }, { name: '琼海' }]
  },
  {
    name: '四川',
    cities: [{ name: '成都' }, { name: '绵阳' }, { name: '德阳' }, { name: '宜宾' }, { name: '南充' }, { name: '泸州' }, { name: '达州' }, { name: '乐山' }, { name: '眉山' }, { name: '自贡' }]
  },
  {
    name: '贵州',
    cities: [{ name: '贵阳' }, { name: '遵义' }, { name: '毕节' }, { name: '黔南' }, { name: '六盘水' }, { name: '黔东南' }]
  },
  {
    name: '云南',
    cities: [{ name: '昆明' }, { name: '曲靖' }, { name: '大理' }, { name: '红河' }, { name: '玉溪' }, { name: '楚雄' }, { name: '昭通' }]
  },
  {
    name: '西藏',
    cities: [{ name: '拉萨' }, { name: '日喀则' }, { name: '昌都' }]
  },
  {
    name: '陕西',
    cities: [{ name: '西安' }, { name: '咸阳' }, { name: '宝鸡' }, { name: '渭南' }, { name: '榆林' }, { name: '汉中' }, { name: '安康' }]
  },
  {
    name: '甘肃',
    cities: [{ name: '兰州' }, { name: '天水' }, { name: '酒泉' }, { name: '武威' }, { name: '庆阳' }, { name: '白银' }]
  },
  {
    name: '青海',
    cities: [{ name: '西宁' }, { name: '海东' }, { name: '格尔木' }]
  },
  {
    name: '宁夏',
    cities: [{ name: '银川' }, { name: '石嘴山' }, { name: '吴忠' }, { name: '中卫' }]
  },
  {
    name: '新疆',
    cities: [{ name: '乌鲁木齐' }, { name: '克拉玛依' }, { name: '伊犁' }, { name: '阿克苏' }, { name: '喀什' }, { name: '昌吉' }]
  },
  {
    name: '台湾',
    cities: [{ name: '台北' }, { name: '高雄' }, { name: '台中' }, { name: '台南' }]
  },
  {
    name: '香港',
    cities: [{ name: '中西区' }, { name: '湾仔区' }, { name: '东区' }, { name: '九龙城' }]
  },
  {
    name: '澳门',
    cities: [{ name: '花地玛堂区' }, { name: '圣安多尼堂区' }, { name: '大堂区' }]
  }
]
