/**
 * Formily × Ant Design Vue 最小桥接（BJ-01 · `_ref/formily-antdv-x3` 对齐子集）
 */
import { Input as AntInput, Select, Switch, Form } from 'ant-design-vue';
import type { Field } from '@formily/core';
import { connect, mapProps } from '@formily/vue';

function asField(field: unknown): Field | undefined {
  if (!field || typeof field !== 'object' || !('address' in field)) return undefined;
  return field as Field;
}

export const FormItem = connect(
  Form.Item,
  mapProps((props, field) => {
    const f = asField(field);
    if (!f || f.display === 'none') return props;
    return {
      ...props,
      label: f.title,
      required: f.required,
      validateStatus: f.validateStatus === 'error' ? 'error' : undefined,
      help: f.selfErrors?.length ? f.selfErrors.join(', ') : undefined,
    };
  }),
);

export const Input = connect(
  AntInput,
  mapProps({ value: 'value', readOnly: 'readonly' }),
);

export const TextArea = connect(AntInput.TextArea, mapProps({ value: 'value' }));

export const FormilySelect = connect(
  Select,
  mapProps({ value: 'value' }, (props, field) => {
    const f = asField(field);
    return {
      ...props,
      options: f?.dataSource ?? props.options,
    };
  }),
);

export const FormilySwitch = connect(
  Switch,
  mapProps({ value: 'checked' }, (props) => {
    const { value, ...rest } = props;
    return rest;
  }),
);
