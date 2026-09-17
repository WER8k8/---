/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { defineComponent, h } from 'vue';
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

const SafeSwitch = defineComponent({
  name: 'SafeSwitch',
  props: ['value', 'checked'],
  emits: ['change', 'update:checked'],
  setup(props, { emit, attrs }) {
    return () =>
      h(Switch, {
        ...attrs,
        checked: props.checked !== undefined ? Boolean(props.checked) : Boolean(props.value),
        'onUpdate:checked': (val: unknown) => {
          emit('update:checked', Boolean(val));
          emit('change', Boolean(val));
        },
      });
  },
});

export const FormilySwitch = connect(SafeSwitch, mapProps({ value: 'checked' }));

