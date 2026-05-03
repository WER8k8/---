const { Op } = require('sequelize');
const { sequelize, models } = require('../config/database');
const Region = models.Region;

const getRegionsTree = async (req, res) => {
  try {
    const [results] = await sequelize.query(`
      SELECT r1.id, r1.name, r1.code, r1.level, r1.status,
             r2.id as child_id, r2.name as child_name, r2.code as child_code, r2.level as child_level,
             r3.id as grandchild_id, r3.name as grandchild_name, r3.code as grandchild_code
      FROM regions r1
      LEFT JOIN regions r2 ON r1.id = r2.parent_id
      LEFT JOIN regions r3 ON r2.id = r3.parent_id
      WHERE r1.level = 1 AND r1.status = 1
      ORDER BY r1.id, r2.id, r3.id
    `);
    
    const tree = buildTree(results);
    res.json({ code: 200, message: 'success', data: tree });
  } catch (error) {
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const getRegionsList = async (req, res) => {
  try {
    const { page = 1, pageSize = 20, level, parentId, keyword, status = 1 } = req.query;
    const offset = (page - 1) * pageSize;
    
    const where = { status };
    if (level) where.level = level;
    if (parentId) where.parentId = parentId;
    if (keyword) where.name = { [Op.like]: `%${keyword}%` };
    
    const { count, rows } = await Region.findAndCountAll({
      where,
      limit: parseInt(pageSize),
      offset,
      order: [['sortOrder', 'ASC'], ['id', 'ASC']]
    });
    
    res.json({
      code: 200,
      message: 'success',
      data: { list: rows, total: count, page: parseInt(page), pageSize: parseInt(pageSize) }
    });
  } catch (error) {
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const batchUpdateStatus = async (req, res) => {
  try {
    const { ids, status } = req.body;
    if (!ids || !Array.isArray(ids) || ids.length === 0) {
      return res.status(400).json({ code: 400, message: '请提供ID列表' });
    }
    
    await Region.update({ status }, { where: { id: ids } });
    res.json({ code: 200, message: '状态更新成功' });
  } catch (error) {
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

function buildTree(flatData) {
  const map = {};
  const roots = [];
  
  flatData.forEach(item => {
    if (!map[item.id]) {
      map[item.id] = { id: item.id, name: item.name, code: item.code, level: item.level, children: [] };
    }
    if (item.child_id) {
      if (!map[item.child_id]) {
        map[item.child_id] = { id: item.child_id, name: item.child_name, code: item.child_code, level: item.child_level, children: [] };
      }
      if (item.grandchild_id) {
        map[item.child_id].children.push({ id: item.grandchild_id, name: item.grandchild_name, code: item.grandchild_code, level: 3 });
      }
      if (!map[item.id].children.find(c => c.id === item.child_id)) {
        map[item.id].children.push(map[item.child_id]);
      }
    }
    if (item.level === 1) roots.push(map[item.id]);
  });
  
  return roots;
}

module.exports = { getRegionsTree, getRegionsList, batchUpdateStatus };
