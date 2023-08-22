import React, { Component } from 'react'
import { render } from 'react-dom'
import CreatableSelect from 'react-select/creatable'
import axios from 'axios'
import { FieldProps } from '@rjsf/utils'

class AffiliationIdentifier extends React.Component {
  constructor (props) {
    super(props)
    this.state = {
      ...props.formData
    }

    // Placeholder for the vocabulary options to be collected externally
    this.options = [{ value: 'https://ror.org/04pp8hn57', label: 'Utrecht University' }]
    this.is_new_affilation = false

    const url = props.uiSchema['ui:data']

    const loadData = async () => {
      const arr = []
      await axios.get(url).then((res) => {
        const result = res.data
        result.map((item) => {
          return arr.push({ value: item.value, label: item.label })
        })
        // Fill options data
        this.options = arr

        // Trigger render.
        this.setState(this.state)
      })
    }
    loadData()
  }

  handleChange = (event) => {
    this.setFormData('Affiliation_Name', event.label)
    this.is_new_affilation = false
    if (event.__isNew__ === undefined || event.__isNew__ === false) {
      this.setFormData('Affiliation_Identifier', event.value)
    } else if (event.__isNew__) {
      this.is_new_affilation = true
    }
  }

  handleChangeIdentifier = (event) => {
    this.setFormData('Affiliation_Identifier', event.target.value)
  }

  setFormData (fieldName, fieldValue) {
    this.setState({
      [fieldName]: fieldValue
    }, () => this.props.onChange(this.state))
  }

  render () {
    const { Affiliation_Name, Affiliation_Identifier } = this.state

    const titleAffiliationName = this.props.schema.properties.Affiliation_Name.title
    const titleAffiliationIdentifier = this.props.schema.properties.Affiliation_Identifier.title

    // let label = <label className='form-label'>{titleAffiliationName}</label>

    const helpAffiliationName = this.props.uiSchema.Affiliation_Name['ui:help']
    const helpAffiliationIdentifier = this.props.uiSchema.Affiliation_Identifier['ui:help']

    let customStyles = {
      control: styles => ({
        ...styles,
        border: '1px solid #ced4da',
        boxShadow: 'none',
        '&:hover': {
          border: '1px solid #ced4da'
        }
      })
    }

    let parentContext = this.props.idSchema.$id
    parentContext = parentContext.replace(this.props.idPrefix + '_', '')
    parentContext = parentContext.replace('_Affiliation_', '')

    const parts = parentContext.split('_')
    parts.pop()
    parentContext = parts.join('_')

    let bothRequired = false
    try {
      bothRequired = this.props.registry.rootSchema.properties[parentContext].items.required.includes('Affiliation')
    } catch (err) {
      bothRequired = false
    }

    let reqName = ''
    let classesName = 'select-box'
    let reqIdf = ''
    let classesIdf = 'form-control'

    const namePresent = !(typeof Affiliation_Name === 'undefined' || Affiliation_Name.length === 0)
    const idfPresent = !(typeof Affiliation_Identifier === 'undefined' || Affiliation_Identifier.length === 0)

    // Identifier is present but Name is not.
    if (idfPresent && !namePresent) {
      reqName = '*'
      classesName += ' is-invalid'
    }

    // Both Name and Identifier are required.
    if (bothRequired) {
      reqName = '*'
      reqIdf = '*'

      if (!namePresent) {
        classesName += ' is-invalid'
      }
      if (!idfPresent) {
        classesIdf += ' is-invalid'
      }
    }

    // Set the customStyle for the select if invalid.
    if (classesName.search('is-invalid') > -1) {
      customStyles = {
        control: styles => ({
          ...styles,
          border: '1px solid #dc3545',
          boxShadow: 'none',
          '&:hover': {
            border: '1px solid #dc3545'
          }
        })
      }
    }

    // Handling of new Affiliation: this overrules all for the identifier field
    // - Identifier is no longer required
    // -a is-invalid indication must be removed.
    if (this.is_new_affilation) {
      reqIdf = ''
      classesIdf = 'form-control'
    }

    let labelClasses = 'form-label'
    if (reqName === '*') {
      labelClasses += ' select-required'
      if (namePresent) {
        // select-filled only has meaning when in combination with select-required (for totalisation of completeness purposes)
        labelClasses += ' select-filled'
      }
    }

    return (
      <div className='d-flex'>
        <div className='col compound-field'>
          <label className={labelClasses}>{titleAffiliationName}{reqName}</label>
          <CreatableSelect
            options={this.options}
            required={reqName === '*'}
            isDisabled={this.props.readonly}
            placeholder={Affiliation_Name}
            onChange={this.handleChange}
            styles={customStyles}
          />
          {helpAffiliationName && (
            <small className='text-muted form-text'>
              <p className='help-block'>{helpAffiliationName}</p>
            </small>
          )}
        </div>

        <div className='col compound-field'>
          <div className='mb-0 form-group'>
            <label className='form-label'>{titleAffiliationIdentifier}{reqIdf}</label>

            {reqIdf === '*' && (
              <input
                type='text'
                required
                className={classesIdf} // 'form-control is-invalid'
                readOnly={this.props.readonly}
                onChange={this.handleChangeIdentifier}
                value={Affiliation_Identifier}
              />)}

            {reqIdf === '' && (
              <input
                type='text'
                className={classesIdf} // 'form-control is-invalid'
                readOnly={this.props.readonly}
                onChange={this.handleChangeIdentifier}
                value={Affiliation_Identifier}
              />)}

            <a className='btn btn-sm btn-primary float-end' href='https://ror.org/search' target='_blank' rel='noreferrer'>
              <i className='fa-solid fa-magnifying-glass' aria-hidden='true' /> Lookup ROR
            </a>

            {helpAffiliationIdentifier && (
              <small className='text-muted form-text'>
                <p className='help-block'>{helpAffiliationIdentifier}</p>
              </small>
            )}
          </div>
        </div>
      </div>
    )
  }
}

export default AffiliationIdentifier