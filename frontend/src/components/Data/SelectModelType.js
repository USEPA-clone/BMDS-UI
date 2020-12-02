import React, {Component} from "react";
import {inject, observer} from "mobx-react";
import PropTypes from "prop-types";

@inject("dataStore")
@observer
class SelectModelType extends Component {
    render() {
        const {dataStore} = this.props;
        return (
            <div className="model-type">
                <label htmlFor="selectmodel">Select Model Type</label>
                <div className="input-group">
                    <select
                        className="form-control mr-1"
                        id="selectmodel"
                        onChange={e => dataStore.setModelType(e.target.value)}>
                        {dataStore.getFilteredModelTypes.map((item, i) => {
                            return (
                                <option key={i} value={item.value}>
                                    {item.name}
                                </option>
                            );
                        })}
                    </select>
                    <div className="input-group-append">
                        <button
                            type="button"
                            className="btn btn-primary btn-sm float-right"
                            disabled={dataStore.checkDatasetsLength}
                            onClick={() => dataStore.addDataset()}>
                            <i className="fa fa-fw fa-plus" />
                            Create
                        </button>
                    </div>
                </div>
            </div>
        );
    }
}
SelectModelType.propTypes = {
    dataStore: PropTypes.object,
    setModelType: PropTypes.func,
    getEditSettings: PropTypes.func,
    getFilteredModelTypes: PropTypes.func,
    addDataset: PropTypes.func,
};
export default SelectModelType;
