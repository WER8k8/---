const { sequelize, models } = require('../config/database');
const Region = models.Region;

const getRegionsTree = async () => {
  const [results] = await sequelize.query(`
    SELECT r1.id, r1.name, r1.code, r1.level, r1.status, r1.sort_order,
           r2.id as child_id, r2.name as child_name, r2.code as child_code, r2.level as child_level,
           r3.id as grandchild_id, r3.name as grandchild_name, r3.code as grandchild_code
    FROM regions r1
    LEFT JOIN regions r2 ON r1.id = r2.parent_id
    LEFT JOIN regions r3 ON r2.id = r3.parent_id
    WHERE r1.level = 1 AND r1.status = 1
    ORDER BY r1.sort_order, r1.id, r2.id, r3.id
  `);
  return buildTree(results);
};

const getRegionsList = async (params = {}) => {
  const { page = 1, pageSize = 20, level, parentId, keyword, status = 1 } = params;
  const { Op } = require('sequelize');
  const where = { status };
  if (level) where.level = level;
  if (parentId) where.parentId = parentId;
  if (keyword) where.name = { [Op.like]: `%${keyword}%` };

  const { count, rows } = await Region.findAndCountAll({
    where,
    limit: parseInt(pageSize),
    offset: (parseInt(page) - 1) * pageSize,
    order: [
      ['sort_order', 'ASC'],
      ['id', 'ASC'],
    ],
  });

  return { list: rows, total: count, page: parseInt(page), pageSize: parseInt(pageSize) };
};

const getRegionById = async id => {
  return await Region.findByPk(id);
};

const createRegion = async data => {
  return await Region.create(data);
};

const updateRegion = async (id, data) => {
  const region = await Region.findByPk(id);
  if (!region) throw new Error('地域不存在');
  return await region.update(data);
};

const deleteRegion = async id => {
  const region = await Region.findByPk(id);
  if (!region) throw new Error('地域不存在');
  await region.destroy();
  return true;
};

const batchUpdateStatus = async (ids, status) => {
  await Region.update({ status }, { where: { id: ids } });
  return true;
};

const getRegionStats = async () => {
  const stats = await Region.findAll({
    attributes: ['level', [sequelize.fn('COUNT', sequelize.col('id')), 'count']],
    where: { status: 1 },
    group: ['level'],
  });
  return stats;
};

function buildTree(flatData) {
  const map = {};
  const roots = [];

  flatData.forEach(item => {
    if (!map[item.id]) {
      map[item.id] = {
        id: item.id,
        name: item.name,
        code: item.code,
        level: item.level,
        children: [],
      };
    }
    if (item.child_id) {
      if (!map[item.child_id]) {
        map[item.child_id] = {
          id: item.child_id,
          name: item.child_name,
          code: item.child_code,
          level: item.child_level,
          children: [],
        };
      }
      if (item.grandchild_id) {
        map[item.child_id].children.push({
          id: item.grandchild_id,
          name: item.grandchild_name,
          code: item.grandchild_code,
          level: 3,
        });
      }
      if (!map[item.id].children.find(c => c.id === item.child_id)) {
        map[item.id].children.push(map[item.child_id]);
      }
    }
    if (item.level === 1) roots.push(map[item.id]);
  });

  return roots;
}

module.exports = {
  getRegionsTree,
  getRegionsList,
  getRegionById,
  createRegion,
  updateRegion,
  deleteRegion,
  batchUpdateStatus,
  getRegionStats,
};
